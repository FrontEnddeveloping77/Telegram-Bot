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
    """Hisobotlar tugmalari — doim ko'rinib turadi (faqat o'zbekcha)."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t(LANG, "btn_monthly_report")),
        KeyboardButton(text=t(LANG, "btn_yearly_report")),
    )
    builder.row(
        KeyboardButton(text=t(LANG, "btn_store_products")),
        KeyboardButton(text=t(LANG, "btn_top_category")),
    )
    builder.row(
        KeyboardButton(text=t(LANG, "btn_daily_report")),
        KeyboardButton(text=t(LANG, "btn_weekly_report")),
    )
    return builder.as_markup(
        resize_keyboard=True,
        is_persistent=True,
    )
