from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.texts import t

LANG = "uz"


def pay_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(LANG, "btn_pay"), callback_data="pay:start")
    return builder.as_markup()


def pricing_keyboard() -> InlineKeyboardMarkup:
    from utils.tariffs import products_selection_keyboard

    return products_selection_keyboard()


def admin_review_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"admin:approve:{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin:reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()


def reports_keyboard(include_payment: bool = False, include_upgrade: bool = False) -> InlineKeyboardMarkup:
    """Guruh va shaxsiy chatlarda bir xilda ishlashi uchun inline (xabar ostidagi)
    tugmalar ishlatiladi — ReplyKeyboardMarkup'dan farqli o'laroq, bu klaviatura
    Telegramning "ochish/yopish" tugmasiga bog'liq emas va Android/iOS/Desktop'da
    barqaror ko'rinadi."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Oylik hisobot", callback_data="rep:monthly"),
        InlineKeyboardButton(text="📈 Yillik hisobot", callback_data="rep:yearly"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Top kategoriya", callback_data="rep:top"),
    )
    builder.row(
        InlineKeyboardButton(text="📅 Kunlik hisobot", callback_data="rep:daily"),
        InlineKeyboardButton(text="📆 Haftalik hisobot", callback_data="rep:weekly"),
    )
    builder.row(
        InlineKeyboardButton(text="🏪 Ombor holati", callback_data="rep:warehouse"),
    )
    builder.row(
        InlineKeyboardButton(text="💸 Jami qarzimiz", callback_data="rep:debt_ours"),
        InlineKeyboardButton(text="👥 Bizga qarzdorlar", callback_data="rep:debtors"),
    )
    if include_upgrade:
        builder.row(
            InlineKeyboardButton(
                text="🚀 Tarifni oshirish (Upgrade)", callback_data="tariff:upgrade_flow"
            )
        )
    if include_payment:
        builder.row(
            InlineKeyboardButton(
                text=t(LANG, "btn_pay"), callback_data="pay:start"
            )
        )
    return builder.as_markup()


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


async def clear_old_reply_keyboard(message) -> None:
    """Foydalanuvchida hali ham oldingi (pastki) ReplyKeyboardMarkup turib qolgan
    bo'lishi mumkin — inline tugmalarga o'tish bu klaviaturani avtomatik olib
    tashlamaydi. Shu sabab bo'sh, ko'rinmas xabar yuborib, uni darhol ReplyKeyboardRemove
    bilan yopamiz, so'ng xabarni o'chirib tashlaymiz."""
    try:
        cleanup = await message.answer("\u2063", reply_markup=ReplyKeyboardRemove())
        await cleanup.delete()
    except Exception:
        pass
