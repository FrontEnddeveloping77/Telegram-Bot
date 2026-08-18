from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.texts import t

LANG = "uz"


def pay_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(LANG, "btn_pay"), callback_data="pay:start")
    return builder.as_markup()


def admin_review_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"admin:approve:{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin:reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()


def reports_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Oylik hisobot"),
        KeyboardButton(text="📈 Yillik hisobot"),
    )
    builder.row(
        KeyboardButton(text="📦 Do'kondagi tovarlar"),
        KeyboardButton(text="🏆 Top kategoriya"),
    )
    builder.row(
        KeyboardButton(text="📅 Kunlik hisobot"),
        KeyboardButton(text="📆 Haftalik hisobot"),
    )
    builder.row(
        KeyboardButton(text="🏪 Ombor holati"),
    )
    return builder.as_markup(resize_keyboard=True, is_persistent=True)
