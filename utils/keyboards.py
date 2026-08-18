from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.texts import t

LANG = "uz"

# Tugma matnlari
BTN_OPEN_MENU = "📋 Menyuni ochish"
BTN_CLOSE_MENU = "❌ Menyuni yopish"


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


def menu_open_keyboard() -> ReplyKeyboardMarkup:
    """Yopiq holat — faqat bitta 'Menyuni ochish' tugmasi."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_OPEN_MENU))
    return builder.as_markup(resize_keyboard=True, is_persistent=False)


def reports_keyboard() -> ReplyKeyboardMarkup:
    """Ochiq holat — to'liq hisobot tugmalari + yopish."""
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
    builder.row(
        KeyboardButton(text=BTN_CLOSE_MENU),
    )
    return builder.as_markup(resize_keyboard=True, is_persistent=False)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
