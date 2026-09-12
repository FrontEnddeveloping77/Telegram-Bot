from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.texts import t
from config import config

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


def reports_keyboard() -> InlineKeyboardMarkup:
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
        InlineKeyboardButton(
            text="📦 Do'kondagi tovarlar", callback_data="rep:products"
        ),
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
    # Sayt va APK havolalari yonma-yon
    if config.website_url and config.apk_url:
        builder.row(
            InlineKeyboardButton(text="🌐 Veb-sayt", url=config.website_url),
            InlineKeyboardButton(text="📱 APK faylini yuklab olish", url=config.apk_url),
        )
    elif config.website_url:
        builder.row(InlineKeyboardButton(text="🌐 Veb-sayt", url=config.website_url))
    elif config.apk_url:
        builder.row(InlineKeyboardButton(text="📱 APK faylini yuklab olish", url=config.apk_url))

    return builder.as_markup()


def app_links_keyboard() -> InlineKeyboardMarkup:
    """Har bir notification uchun sayt va APK havolalarini yonma-yon chiqaradi."""
    builder = InlineKeyboardBuilder()
    if config.website_url and config.apk_url:
        builder.row(
            InlineKeyboardButton(text="🌐 Veb-sayt", url=config.website_url),
            InlineKeyboardButton(text="📱 APK faylini yuklab olish", url=config.apk_url),
        )
    elif config.website_url:
        builder.row(InlineKeyboardButton(text="🌐 Veb-sayt", url=config.website_url))
    elif config.apk_url:
        builder.row(InlineKeyboardButton(text="📱 APK faylini yuklab olish", url=config.apk_url))
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
