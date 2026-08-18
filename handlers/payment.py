import json
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import config
from database.requests import (
    get_user,
    renew_or_activate_subscription,
    create_payment_request,
    get_payment_request,
    set_payment_request_admin_messages,
    claim_payment_request,
    finalize_payment_rejection,
    finalize_payment_approval,
)
from locales.texts import t
from utils.keyboards import admin_review_keyboard, menu_open_keyboard
from utils.credentials import (
    generate_unique_login,
    generate_strong_password,
    encrypt_password,
    decrypt_password,
    hash_password_for_site,
)

router = Router(name="payment")
logger = logging.getLogger(__name__)


class PaymentStates(StatesGroup):
    waiting_for_receipt = State()


class AdminStates(StatesGroup):
    waiting_for_reject_reason = State()


def _formatted_price() -> str:
    return f"{config.product_price:,}".replace(",", " ")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in config.admin_ids


# ===================== Foydalanuvchi tomoni =====================


@router.callback_query(F.data == "pay:start")
async def on_pay_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    language = user.language if user else "uz"

    if user and user.is_paid:
        password = decrypt_password(user.site_password_encrypted)
        await callback.message.answer(
            t(
                language,
                "already_paid",
                website=config.website_url,
                login=user.site_login,
                password=password,
            )
        )
        await callback.answer()
        return

    await callback.message.answer(
        t(
            language,
            "card_payment_instructions",
            card_number=config.card_number,
            card_holder=config.card_holder_name,
            price=_formatted_price(),
        )
    )
    await state.set_state(PaymentStates.waiting_for_receipt)
    await callback.answer()


@router.message(PaymentStates.waiting_for_receipt, F.photo)
async def on_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    user = await get_user(message.from_user.id)
    language = user.language if user else "uz"

    receipt_file_id = message.photo[-1].file_id
    payment_request = await create_payment_request(
        telegram_id=message.from_user.id,
        receipt_file_id=receipt_file_id,
    )

    await state.clear()
    await message.answer(t(language, "receipt_received"))

    if not config.admin_ids:
        logger.warning(
            "ADMIN_IDS bo'sh — to'lov cheklarini hech kimga yubora olmayapman"
        )
        return

    caption = t(
        language,
        "admin_new_payment_request",
        full_name=message.from_user.full_name,
        username=message.from_user.username or "-",
        telegram_id=message.from_user.id,
        price=_formatted_price(),
    )

    admin_message_ids: dict[int, int] = {}
    for admin_id in config.admin_ids:
        try:
            sent = await bot.send_photo(
                admin_id,
                receipt_file_id,
                caption=caption,
                reply_markup=admin_review_keyboard(payment_request.id),
            )
            admin_message_ids[admin_id] = sent.message_id
        except Exception:
            logger.exception("Adminга chek yuborishda xatolik: %s", admin_id)

    await set_payment_request_admin_messages(payment_request.id, admin_message_ids)


@router.message(PaymentStates.waiting_for_receipt)
async def on_receipt_invalid(message: Message):
    user = await get_user(message.from_user.id)
    language = user.language if user else "uz"
    await message.answer(t(language, "receipt_invalid"))


# ===================== Admin tomoni =====================


async def _sync_admin_messages(
    bot: Bot, payment_request, caption_suffix: str, remove_buttons: bool = True
):
    """Barcha adminlarga yuborilgan xabarlarni yangi holatga mos yangilaydi."""
    if not payment_request.admin_message_ids:
        return
    try:
        admin_message_ids = json.loads(payment_request.admin_message_ids)
    except (TypeError, ValueError):
        return

    user = await get_user(payment_request.telegram_id)
    language = user.language if user else "uz"
    base_caption = t(
        language,
        "admin_new_payment_request",
        full_name=(user.full_name if user and user.full_name else "-"),
        username=(user.username if user and user.username else "-"),
        telegram_id=payment_request.telegram_id,
        price=_formatted_price(),
    )

    for admin_id_str, message_id in admin_message_ids.items():
        try:
            await bot.edit_message_caption(
                chat_id=int(admin_id_str),
                message_id=message_id,
                caption=base_caption + caption_suffix,
                reply_markup=None
                if remove_buttons
                else admin_review_keyboard(payment_request.id),
            )
        except Exception:
            logger.exception("Admin xabarini yangilashda xatolik: %s", admin_id_str)


@router.callback_query(F.data.startswith("admin:approve:"))
async def on_admin_approve(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda ruxsat yo'q", show_alert=True)
        return

    request_id = int(callback.data.split(":")[2])

    payment_request = await claim_payment_request(
        request_id, callback.from_user.id, new_status="approved", from_status="pending"
    )
    if payment_request is None:
        await callback.answer(t("uz", "admin_already_handled"), show_alert=True)
        return

    await callback.answer()

    target_user = await get_user(payment_request.telegram_id)
    if not target_user:
        logger.error("PaymentRequest %s uchun user topilmadi", request_id)
        return
    language = target_user.language or "uz"

    candidate_login = await generate_unique_login()
    candidate_password = generate_strong_password()
    candidate_password_encrypted = encrypt_password(candidate_password)
    candidate_password_hash = hash_password_for_site(candidate_password)

    login, password_encrypted = await renew_or_activate_subscription(
        telegram_id=payment_request.telegram_id,
        payment_method="card",
        payment_id=f"CARD-{payment_request.id}",
        new_login=candidate_login,
        new_password_encrypted=candidate_password_encrypted,
        new_password_hash=candidate_password_hash,
    )

    # Har doim asl (bir marta yaratilgan, o'zgarmas) parolni ko'rsatamiz
    password = decrypt_password(password_encrypted)

    try:
        await bot.send_message(
            payment_request.telegram_id,
            t(
                language,
                "payment_success",
                website=config.website_url,
                login=login,
                password=password,
            ),
            reply_markup=menu_open_keyboard(),
        )
    except Exception:
        logger.exception("Userga tasdiqlash xabarini yuborishda xatolik")

    await finalize_payment_approval(request_id)

    admin_name = callback.from_user.full_name
    await _sync_admin_messages(
        bot,
        payment_request,
        t("uz", "admin_approved_caption_suffix", admin_name=admin_name),
    )


@router.callback_query(F.data.startswith("admin:reject:"))
async def on_admin_reject(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda ruxsat yo'q", show_alert=True)
        return

    request_id = int(callback.data.split(":")[2])

    payment_request = await claim_payment_request(
        request_id, callback.from_user.id, new_status="rejecting", from_status="pending"
    )
    if payment_request is None:
        await callback.answer(t("uz", "admin_already_handled"), show_alert=True)
        return

    await callback.answer()

    admin_name = callback.from_user.full_name
    await _sync_admin_messages(
        bot,
        payment_request,
        t("uz", "admin_pending_reason_caption_suffix", admin_name=admin_name),
    )

    await state.set_state(AdminStates.waiting_for_reject_reason)
    await state.update_data(payment_request_id=request_id)
    await callback.message.answer(t("uz", "admin_ask_reject_reason"))


@router.message(AdminStates.waiting_for_reject_reason, F.text)
async def on_reject_reason_provided(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_id = data.get("payment_request_id")
    await state.clear()

    if request_id is None:
        return

    payment_request = await get_payment_request(request_id)
    if payment_request is None or payment_request.status != "rejecting":
        return

    reason = message.text.strip()
    await finalize_payment_rejection(request_id, reason)

    target_user = await get_user(payment_request.telegram_id)
    language = target_user.language if target_user else "uz"

    try:
        await bot.send_message(
            payment_request.telegram_id,
            t(language, "payment_rejected_user", reason=reason),
        )
    except Exception:
        logger.exception("Userga rad etish xabarini yuborishda xatolik")

    await message.answer(t("uz", "admin_reject_reason_saved"))

    admin_name = message.from_user.full_name
    payment_request = await get_payment_request(request_id)
    await _sync_admin_messages(
        bot,
        payment_request,
        t("uz", "admin_rejected_caption_suffix", admin_name=admin_name, reason=reason),
    )
