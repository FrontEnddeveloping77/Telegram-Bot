from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import (
    get_or_create_user,
    set_language,
    get_user,
    get_user_by_group_chat_id,
    set_user_tariff,
)
from locales.texts import t
from utils.keyboards import (
    reports_keyboard,
    clear_old_reply_keyboard,
)
from utils.credentials import decrypt_password
from utils.tariffs import (
    products_selection_keyboard,
    groups_selection_keyboard,
    tariff_confirmation_keyboard,
    upgrade_confirmation_keyboard,
    calculate_tariff_price,
    calculate_upgrade_proration,
    format_price,
    get_admin_contact_url,
    ADMIN_CONTACT_URL,
)

router = Router(name="start")

LANG = "uz"  # Bot faqat o'zbekcha


async def send_welcome_offer(message: Message, name: str) -> None:
    await message.answer(
        t(
            LANG,
            "welcome_offer",
            name=name,
        ),
        reply_markup=products_selection_keyboard(),
    )


async def send_active_subscription_info(message: Message, user) -> None:
    """Obuna faol bo'lganda login/parolni ko'rsatadi va hisobot tugmalarini chiqaradi."""
    password = decrypt_password(user.site_password_encrypted)
    await clear_old_reply_keyboard(message)

    info_text = t(
        LANG,
        "already_paid",
        login=user.site_login,
        password=password,
    )
    if user.max_products and user.max_groups:
        group_label = (
            "1 ta guruh"
            if user.max_groups == 1
            else ("2 ta guruh" if user.max_groups == 2 else "3-5 ta guruh")
        )
        info_text += (
            f"\n\n📦 Tarif: <b>{format_price(user.max_products)} tagacha ID</b>"
            f"\n👥 Guruh limiti: <b>{group_label}</b>"
        )
        if user.expires_at:
            now = datetime.now(timezone.utc)
            rem_days = max(1, (user.expires_at.date() - now.date()).days)
            info_text += f"\n⏳ Qolgan muddat: <b>{rem_days} kun</b>"

    await message.answer(
        info_text,
        reply_markup=reports_keyboard(include_payment=True, include_upgrade=True),
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

    is_first_time = not user.language_selected
    if is_first_time:
        await set_language(message.from_user.id, LANG)

    user = await get_user(message.from_user.id)
    await state.clear()

    if user and user.is_paid and (
        user.expires_at is None or user.expires_at > datetime.now(timezone.utc)
    ):
        await send_active_subscription_info(message, user)
        return

    await send_welcome_offer(message, message.from_user.full_name)


@router.message(Command("tariflar"))
async def cmd_tariffs(message: Message):
    """Foydalanuvchi istalgan payt tariflarni ko'rishi va tanlashi mumkin."""
    await message.answer(
        t(LANG, "welcome_offer", name=message.from_user.full_name),
        reply_markup=products_selection_keyboard(),
    )


# ===================== Tarif tanlash CallbackQuery'lari =====================


@router.callback_query(F.data == "tariff:upgrade_flow")
async def on_upgrade_flow(callback: CallbackQuery):
    """Faol obunachi tarifini oshirishni boshlaganda."""
    text = (
        "🚀 <b>Tarifingizni oshirish (Upgrade):</b>\n\n"
        "Qaysi tovar (ID) oralig'iga o'tmoqchisiz? Tanlang 👇"
    )
    markup = products_selection_keyboard()
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "tariff:cancel_upgrade")
async def on_cancel_upgrade(callback: CallbackQuery, state: FSMContext):
    """Oshirishni bekor qilish."""
    await state.clear()
    user = await get_user(callback.from_user.id)
    if user and user.is_paid and (
        user.expires_at is None or user.expires_at > datetime.now(timezone.utc)
    ):
        await callback.message.delete()
        await send_active_subscription_info(callback.message, user)
    else:
        text = "📦 <b>Do'koningizdagi tovar turlari (ID) sonini tanlang:</b>"
        markup = products_selection_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except Exception:
            await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:prod:"))
async def on_product_tier_selected(callback: CallbackQuery):
    """Foydalanuvchi tovar soni (ID) oralig'ini tanlaganda ishlaydi."""
    parts = callback.data.split(":")
    max_products = int(parts[2])

    text = t(
        LANG,
        "select_group_count",
        products=format_price(max_products),
    )
    markup = groups_selection_keyboard(max_products)

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "tariff:back_to_products")
async def on_back_to_products(callback: CallbackQuery):
    """Tovar tanlash bosqichiga qaytish."""
    text = (
        "📦 <b>1-qadam: Do'koningizdagi tovar turlari (ID) sonini tanlang:</b>\n\n"
        "O'zingizga mos tovar oralig'ini tanlang 👇"
    )
    markup = products_selection_keyboard()

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:select:"))
async def on_tariff_selected(callback: CallbackQuery, state: FSMContext):
    """Tovar va guruh soni tanlanganda."""
    parts = callback.data.split(":")
    max_products = int(parts[2])
    max_groups = int(parts[3])

    price = calculate_tariff_price(max_products, max_groups)
    if price is None:
        await callback.answer("Tarif topilmadi", show_alert=True)
        return

    group_label = (
        "1 ta guruh"
        if max_groups == 1
        else ("2 ta guruh" if max_groups == 2 else "3-5 ta guruh")
    )

    user = await get_user(callback.from_user.id)
    now = datetime.now(timezone.utc)
    is_active = (
        user
        and user.is_paid
        and user.expires_at
        and user.expires_at > now
    )

    # Agar foydalanuvchida hozir faol obuna bo'lsa — tarifni oshirish (Upgrade) logikasi ishlaydi
    if is_active:
        current_price = user.tariff_price or calculate_tariff_price(
            user.max_products or 1000, user.max_groups or 1
        ) or 299_000

        if price > current_price:
            proration = calculate_upgrade_proration(
                old_monthly_price=current_price,
                new_monthly_price=price,
                expires_at=user.expires_at,
            )

            if proration:
                days = proration["remaining_days"]
                old_prod = user.max_products or 1000
                old_grp = user.max_groups or 1
                old_label = (
                    "1 ta guruh"
                    if old_grp == 1
                    else ("2 ta guruh" if old_grp == 2 else "3-5 ta guruh")
                )

                # Upgrade holatini saqlash
                await state.update_data(
                    is_upgrade=True,
                    upgrade_products=max_products,
                    upgrade_groups=max_groups,
                    upgrade_price=price,
                    expected_amount=proration["upgrade_amount"],
                    remaining_days=days,
                )

                upgrade_text = (
                    f"🚀 <b>TARIFNI OSHIRISH (UPGRADE)</b>\n\n"
                    f"📋 <b>Amaldagi tarifingiz:</b> {format_price(old_prod)} tagacha ID ({old_label})\n"
                    f"⏳ <b>Obuna muddatingiz tugashiga:</b> <b>{days} kun</b> qolgan\n\n"
                    f"📦 <b>Yangi tanlangan tarif:</b> <b>{format_price(max_products)} tagacha ID</b> ({group_label})\n\n"
                    f"📊 <b>Qayta hisob-kitob (qolgan {days} kun uchun):</b>\n"
                    f"• Amaldagi tarifingizning {days} kunlik qiymati: <b>{proration['formatted_old_remaining']} so'm</b>\n"
                    f"• Yangi tarifingizning {days} kunlik qiymati: <b>{proration['formatted_new_remaining']} so'm</b>\n"
                    f"• 💰 <b>To'lanadigan farq:</b> <b>{proration['formatted_upgrade_amount']} so'm</b>\n\n"
                    f"ℹ️ <i>Siz faqat qolgan {days} kun uchun <b>{proration['formatted_upgrade_amount']} so'm</b> to'laysiz. "
                    f"To'lov tasdiqlangach, tarifingiz zudlik bilan {format_price(max_products)} tagacha ID ga oshiriladi va qolgan muddat saqlanib qoladi!</i>"
                )
                markup = upgrade_confirmation_keyboard(proration["upgrade_amount"])
                try:
                    await callback.message.edit_text(upgrade_text, reply_markup=markup)
                except Exception:
                    await callback.message.answer(upgrade_text, reply_markup=markup)
                await callback.answer()
                return

        elif price <= current_price:
            downgrade_text = (
                f"ℹ️ Siz hozirda <b>{format_price(user.max_products or 1000)} tagacha ID</b> "
                f"tarifidasiz (oylik to'lov: {format_price(current_price)} so'm).\n\n"
                f"Tarifni pasaytirish faqat joriy obuna muddati tugagandan so'ng amalga oshiriladi.\n\n"
                f"Agar tovar yoki guruh limitini oshirmoqchi bo'lsangiz, yuqoriroq tarifni tanlang "
                f"yoki adminga murojaat qiling: @ABDULAZIZ_AVAZOV"
            )
            b = InlineKeyboardBuilder()
            b.button(text="🔄 Boshqa tarif tanlash", callback_data="tariff:back_to_products")
            b.button(
                text="💬 Adminga murojaat qilish",
                url=get_admin_contact_url("Assalomu alaykum! Tarifimni o'zgartirish bo'yicha yordam kerak edi."),
            )
            b.button(text="⬅️ Bekor qilish", callback_data="tariff:cancel_upgrade")
            b.adjust(1)
            try:
                await callback.message.edit_text(downgrade_text, reply_markup=b.as_markup())
            except Exception:
                await callback.message.answer(downgrade_text, reply_markup=b.as_markup())
            await callback.answer()
            return

    # Yangi foydalanuvchi yoki muddati o'tgan foydalanuvchi uchun odatiy to'liq to'lov
    await state.clear()
    await set_user_tariff(
        telegram_id=callback.from_user.id,
        max_products=max_products,
        max_groups=max_groups,
        price=price,
    )

    summary_text = t(
        LANG,
        "tariff_selected_summary",
        products=format_price(max_products),
        groups=group_label,
        price=format_price(price),
    )
    markup = tariff_confirmation_keyboard(max_products, max_groups)

    try:
        await callback.message.edit_text(summary_text, reply_markup=markup)
    except Exception:
        await callback.message.answer(summary_text, reply_markup=markup)
    await callback.answer()
