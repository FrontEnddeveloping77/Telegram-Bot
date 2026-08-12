from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
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


def payment_methods_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_click"), callback_data="pay:method:click")
    builder.button(text=t(language, "btn_payme"), callback_data="pay:method:payme")
    builder.button(text=t(language, "btn_other"), callback_data="pay:method:other")
    builder.adjust(2, 1)
    return builder.as_markup()
