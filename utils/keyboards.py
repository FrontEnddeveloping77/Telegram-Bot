from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.texts import t


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.adjust(1)
    return builder.as_markup()


def pay_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_pay"), callback_data="pay:start")
    return builder.as_markup()


def admin_review_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"admin:approve:{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin:reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()


def reports_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Hisobotlar uchun asosiy kategoriya tugmalari (Reply keyboard)."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=t(language, "btn_monthly_report"))
    builder.button(text=t(language, "btn_yearly_report"))
    builder.button(text=t(language, "btn_store_products"))
    builder.button(text=t(language, "btn_top_category"))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)
