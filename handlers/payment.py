import json
import logging
from datetime import datetime, timezone

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
from utils.keyboards import admin_review_keyboard, reports_keyboard
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


def _formatted_price(amount: int | None = None) -> str:
    return f"{amount if amount is not None else config.product_price:,}".replace(",", " ")


async def _price_for_user(user) -> int | None:
    if user.tariff_price:
        return user.tariff_price
    if user.max_products and user.max_groups:
        from utils.tariffs import calculate_tariff_price

        return calculate_tariff_price(user.max_products, user.max_groups)
    if config.product_price and config.product_price > 0:
        return config.product_price
    return None


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in config.admin_ids


# ===================== Foydalanuvchi tomoni =====================


@router.callback_query(F.data == "pay:start")
async def on_pay_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    language = user.language if user else "uz"

    state_data = await state.get_data()
    is_upgrade = state_data.get("is_upgrade", False)

    if (
        user
        and user.is_paid
        and not is_upgrade
        and user.payment_method != "trial"
        and (user.expires_at is None or user.expires_at > datetime.now(timezone.utc))
    ):
        password = decrypt_password(user.site_password_encrypted)
        await callback.message.answer(
            t(
                language,
                "already_paid",
                login=user.site_login,
                password=password,
            )
        )
        await callback.answer()
        return

    from utils.tariffs import format_price

    if is_upgrade:
        expected_amount = state_data.get("expected_amount")
        upgrade_products = state_data.get("upgrade_products")
        upgrade_groups = state_data.get("upgrade_groups")
        remaining_days = state_data.get("remaining_days", 1)
        group_lbl = (
            "1 ta guruh"
            if upgrade_groups == 1
            else ("2 ta guruh" if upgrade_groups == 2 else "3-5 ta guruh")
        )

        instructions = (
            f"💳 <b>Tarifni oshirish uchun to'lov:</b>\n\n"
            f"📦 Yangi tarif: <b>{format_price(upgrade_products)} tagacha ID</b> ({group_lbl})\n"
            f"⏳ Qolgan muddat: <b>{remaining_days} kun</b>\n"
            f"💰 To'lanadigan farq summasi: <b>{_formatted_price(expected_amount)} so'm</b>\n\n"
            f"Karta raqami: <code>{config.card_number}</code>\n"
            f"Karta egasi: <b>{config.card_holder_name}</b>\n\n"
            f"1️⃣ Karta raqamini bosib nusxa oling (copy)\n"
            f"2️⃣ <b>{_formatted_price(expected_amount)} so'm</b> to'lovni amalga oshiring\n"
            f"3️⃣ To'lov chekini (screenshot yoki rasm) shu yerga yuboring 👇"
        )
        await callback.message.answer(instructions)
        await state.set_state(PaymentStates.waiting_for_receipt)
        await callback.answer()
        return

    if not user:
        from utils.tariffs import products_selection_keyboard

        await callback.message.answer(
            "Iltimos, avval o'zingizga mos tarifni tanlang 👇",
            reply_markup=products_selection_keyboard(),
        )
        await callback.answer()
        return

    expected_amount = await _price_for_user(user)
    if expected_amount is None or expected_amount < 1:
        from utils.tariffs import products_selection_keyboard

        await callback.message.answer(
            "Iltimos, avval o'zingizga mos tarifni tanlang 👇",
            reply_markup=products_selection_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        t(
            language,
            "card_payment_instructions",
            card_number=config.card_number,
            card_holder=config.card_holder_name,
            price=_formatted_price(expected_amount),
        )
    )
    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(expected_amount=expected_amount)
    await callback.answer()


@router.message(PaymentStates.waiting_for_receipt, F.photo)
async def on_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    user = await get_user(message.from_user.id)
    language = user.language if user else "uz"
    state_data = await state.get_data()
    expected_amount = state_data.get("expected_amount")
    is_upgrade = state_data.get("is_upgrade", False)
    upgrade_products = state_data.get("upgrade_products")
    upgrade_groups = state_data.get("upgrade_groups")
    upgrade_price = state_data.get("upgrade_price")

    receipt_file_id = message.photo[-1].file_id
    payment_request = await create_payment_request(
        telegram_id=message.from_user.id,
        receipt_file_id=receipt_file_id,
        expected_amount=expected_amount,
        is_upgrade=is_upgrade,
        upgrade_products=upgrade_products,
        upgrade_groups=upgrade_groups,
        upgrade_price=upgrade_price,
    )

    await state.clear()
    await message.answer(t(language, "receipt_received"))

    if not config.admin_ids:
        logger.warning(
            "ADMIN_IDS bo'sh — to'lov cheklarini hech kimga yubora olmayapman"
        )
        return

    from utils.tariffs import format_price

    if is_upgrade:
        group_lbl = (
            "1 ta guruh"
            if upgrade_groups == 1
            else ("2 ta guruh" if upgrade_groups == 2 else "3-5 ta guruh")
        )
        caption = (
            f"🔄 <b>YANGI TO'LOV CHEKI (TARIFNI OSHIRISH)!</b>\n\n"
            f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
            f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n"
            f"📦 Yangi tarif: <b>{format_price(upgrade_products)} tagacha ID ({group_lbl})</b>\n"
            f"💰 Kutilayotgan farq summasi: <b>{_formatted_price(expected_amount)} so'm</b>\n\n"
            f"Chekni tekshirib, quyidagi tugmalardan birini tanlang 👇"
        )
    else:
        tariff_desc = (
            f"{user.max_products:,} tagacha ID, {user.max_groups} ta guruh".replace(",", " ")
            if (user and user.max_products and user.max_groups)
            else "-"
        )
        caption = t(
            language,
            "admin_new_payment_request",
            full_name=message.from_user.full_name,
            username=message.from_user.username or "-",
            telegram_id=message.from_user.id,
            tariff=tariff_desc,
            price=_formatted_price(expected_amount),
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

    if payment_request.is_upgrade:
        from utils.tariffs import format_price

        group_lbl = (
            "1 ta guruh"
            if payment_request.upgrade_groups == 1
            else ("2 ta guruh" if payment_request.upgrade_groups == 2 else "3-5 ta guruh")
        )
        base_caption = (
            f"🔄 <b>Yangi to'lov cheki (TARIFNI OSHIRISH)!</b>\n\n"
            f"👤 Foydalanuvchi: {(user.full_name if user and user.full_name else '-')}"
            f" (@{user.username if user and user.username else '-'})\n"
            f"🆔 Telegram ID: <code>{payment_request.telegram_id}</code>\n"
            f"📦 Yangi tarif: <b>{format_price(payment_request.upgrade_products)} tagacha ID ({group_lbl})</b>\n"
            f"💰 Kutilayotgan farq summasi: {_formatted_price(payment_request.expected_amount)} so'm"
        )
    else:
        tariff_desc = (
            f"{user.max_products:,} tagacha ID, {user.max_groups} ta guruh".replace(",", " ")
            if (user and user.max_products and user.max_groups)
            else "-"
        )
        base_caption = t(
            language,
            "admin_new_payment_request",
            full_name=(user.full_name if user and user.full_name else "-"),
            username=(user.username if user and user.username else "-"),
            telegram_id=payment_request.telegram_id,
            tariff=tariff_desc,
            price=_formatted_price(payment_request.expected_amount),
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

    if payment_request.is_upgrade:
        from database.requests import apply_tariff_upgrade
        from utils.tariffs import format_price

        await apply_tariff_upgrade(
            telegram_id=payment_request.telegram_id,
            new_products=payment_request.upgrade_products or 1000,
            new_groups=payment_request.upgrade_groups or 1,
            new_price=payment_request.upgrade_price or 299_000,
        )
        group_lbl = (
            "1 ta guruh"
            if payment_request.upgrade_groups == 1
            else ("2 ta guruh" if payment_request.upgrade_groups == 2 else "3-5 ta guruh")
        )
        try:
            await bot.send_message(
                payment_request.telegram_id,
                f"✅ <b>Tarifingiz muvaffaqiyatli oshirildi!</b>\n\n"
                f"📦 Yangi tovar limiti: <b>{format_price(payment_request.upgrade_products)} tagacha ID</b>\n"
                f"👥 Yangi guruh limiti: <b>{group_lbl}</b>\n\n"
                f"Amaldagi obuna muddati saqlanib qoldi va yangi limitlaringiz zudlik bilan kuchga kirdi!",
                reply_markup=reports_keyboard(include_upgrade=True),
            )
        except Exception:
            logger.exception("Userga tarif oshirish tasdiq xabarini yuborishda xatolik")
    else:
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
                    login=login,
                    password=password,
                ),
                reply_markup=reports_keyboard(include_upgrade=True),
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
