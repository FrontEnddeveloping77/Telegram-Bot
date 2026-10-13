from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType

from database.requests import (
    get_or_create_user,
    set_language,
    get_user,
    get_user_by_group_chat_id,
    select_pricing_model,
    update_product_count,
    activate_trial,
)
from locales.texts import t
from utils.keyboards import (
    pay_keyboard,
    pricing_keyboard,
    reports_keyboard,
    clear_old_reply_keyboard,
)
from utils.credentials import (
    decrypt_password,
    generate_unique_login,
    generate_strong_password,
    encrypt_password,
    hash_password_for_site,
)

router = Router(name="start")

LANG = "uz"  # Bot faqat o'zbekcha


class PricingStates(StatesGroup):
    waiting_for_shop_count = State()
    waiting_for_product_count = State()


async def send_welcome_offer(message: Message, name: str) -> None:
    await message.answer(
        t(
            LANG,
            "welcome_offer",
            name=name,
        ),
        reply_markup=pricing_keyboard(),
    )


async def send_active_subscription_info(message: Message, user) -> None:
    """Obuna faol bo'lganda login/parolni ko'rsatadi va hisobot tugmalarini chiqaradi."""
    password = decrypt_password(user.site_password_encrypted)
    await clear_old_reply_keyboard(message)
    await message.answer(
        t(
            LANG,
            "already_paid",
            login=user.site_login,
            password=password,
        ),
        reply_markup=reports_keyboard(include_payment=True),
    )

@router.message(CommandStart(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def cmd_start_in_group(message: Message):
    """Guruhda /start — faqat bog'lanish holati."""
    linked_user = await get_user_by_group_chat_id(message.chat.id)

    if linked_user:
        await clear_old_reply_keyboard(message)
        await message.answer(
            "✅ Bu guruh allaqachon bog'langan.\n"
            "Saytdagi o'zgarishlar (mahsulot, rasxod va h.k.) shu guruhga avtomatik yuborib turiladi.\n"
            "Hisobotlar uchun chap tomondagi <b>Menu</b> tugmasidan foydalaning yoki /menu bosing.",
            reply_markup=reports_keyboard(),
        )
    else:
        await message.answer(
            "🔗 Bu guruhni saytdagi hisobingizga bog'lash uchun, guruh admini "
            "login va parolni quyidagi formatda yuborsin:\n\n"
            "<code>login parol</code>\n\n"
            "Masalan: <code>user482913 aB3xY9Zk1Qw2</code>"
        )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    # Til tanlash yo'q — doim o'zbekcha
    is_first_time = not user.language_selected
    if is_first_time:
        await set_language(message.from_user.id, LANG)

    # Yangilangan user
    user = await get_user(message.from_user.id)
    await state.clear()

    if user and user.is_paid and (
        user.expires_at is None or user.expires_at > datetime.now(timezone.utc)
    ):
        await send_active_subscription_info(message, user)
        return

    await state.set_state(PricingStates.waiting_for_shop_count)
    await send_welcome_offer(message, message.from_user.full_name)


async def _select_plan(
    callback: CallbackQuery, state: FSMContext, pricing_model: str
) -> None:
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    await select_pricing_model(callback.from_user.id, pricing_model)
    trial_started = False
    if not user.site_login:
        plain_password = generate_strong_password()
        trial_user = await activate_trial(
            telegram_id=callback.from_user.id,
            new_login=await generate_unique_login(),
            new_password_encrypted=encrypt_password(plain_password),
            new_password_hash=hash_password_for_site(plain_password),
        )
        trial_started = trial_user is not None

    user = await get_user(callback.from_user.id)
    if not user:
        await callback.message.answer(
            "Akkaunt ochishda xatolik yuz berdi. Qayta urinib ko'ring."
        )
        await callback.answer()
        return

    is_active = user.is_paid and (
        user.expires_at is None or user.expires_at > datetime.now(timezone.utc)
    )
    if is_active and (not user.site_login or not user.site_password_encrypted):
        await callback.message.answer(
            "Akkaunt ochishda xatolik yuz berdi. Qayta urinib ko'ring."
        )
        await callback.answer()
        return

    plan_key = "pricing_profit" if pricing_model == "profit" else "pricing_products"
    plan_text = t(LANG, plan_key)
    if trial_started or is_active:
        password = decrypt_password(user.site_password_encrypted)
        credential_key = "trial_credentials" if trial_started else "existing_credentials"
        plan_text += "\n\n" + t(
            LANG,
            credential_key,
            login=user.site_login,
            password=password,
        )
        reply_markup = reports_keyboard(include_payment=True)
    else:
        plan_text += "\n\n" + t(LANG, "trial_expired")
        reply_markup = pay_keyboard()

    await callback.message.answer(plan_text, reply_markup=reply_markup)

    if pricing_model == "products":
        if user.product_count:
            price = ((user.product_count + 99) // 100) * 50_000
            await callback.message.answer(
                t(
                    LANG,
                    "product_count_saved",
                    count=user.product_count,
                    price=f"{price:,}".replace(",", " "),
                )
            )
            await state.clear()
        else:
            await state.set_state(PricingStates.waiting_for_product_count)
            await callback.message.answer(t(LANG, "ask_product_count"))
    else:
        await state.clear()
    await callback.answer()


@router.callback_query(F.data == "pricing:profit")
async def on_profit_pricing(callback: CallbackQuery, state: FSMContext):
    await _select_plan(callback, state, "profit")


@router.callback_query(F.data == "pricing:products")
async def on_product_pricing(callback: CallbackQuery, state: FSMContext):
    await _select_plan(callback, state, "products")


@router.message(PricingStates.waiting_for_product_count, F.text)
async def on_product_count(message: Message, state: FSMContext):
    try:
        product_count = int(message.text.strip())
        if product_count <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(t(LANG, "invalid_product_count"))
        return

    await update_product_count(message.from_user.id, product_count)
    price = ((product_count + 99) // 100) * 50_000
    await message.answer(
        t(
            LANG,
            "product_count_saved",
            count=product_count,
            price=f"{price:,}".replace(",", " "),
        )
    )
    await state.clear()


@router.message(PricingStates.waiting_for_shop_count, F.text)
async def on_shop_count(message: Message, state: FSMContext):
    try:
        product_count = int(message.text.strip())
        if product_count <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(t(LANG, "invalid_product_count"))
        return

    await update_product_count(message.from_user.id, product_count)
    await message.answer(t(LANG, "product_count_received"))
    await state.clear()
