import os
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile

from config import config
from database.requests import get_or_create_user, set_language, get_user
from locales.texts import t
from utils.keyboards import language_keyboard, pay_keyboard
from utils.credentials import decrypt_password

router = Router(name="start")
logger = logging.getLogger(__name__)


async def send_welcome_offer(message: Message, language: str, name: str) -> None:
    await message.answer(
        t(
            language,
            "welcome_offer",
            name=name,
            price=f"{config.product_price:,}".replace(",", " "),
        ),
        reply_markup=pay_keyboard(language),
    )


async def send_active_subscription_info(message: Message, user) -> None:
    """Obuna faol bo'lganda login/parolni (shifrdan ochib) qayta ko'rsatadi."""
    password = decrypt_password(user.site_password_encrypted)
    await message.answer(
        t(
            user.language,
            "already_paid",
            website=config.website_url,
            login=user.site_login,
            password=password,
        )
    )


async def send_tutorial_video(message: Message, language: str) -> None:
    """Birinchi marta /start bosilganda qo'llanma videosini yuboradi (agar fayl mavjud bo'lsa)."""
    if not config.video_path or not os.path.exists(config.video_path):
        logger.warning("Qo'llanma video fayli topilmadi: %s", config.video_path)
        return
    try:
        video = FSInputFile(config.video_path)
        await message.answer_video(video, caption=t(language, "tutorial_caption"))
    except Exception:
        logger.exception("Video yuborishda xatolik")


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if not user.language_selected:
        # Faqat birinchi marta /start bosilganda til tanlash chiqadi
        await message.answer(
            t("uz", "choose_language"),
            reply_markup=language_keyboard(),
        )
        return

    if user.is_paid:
        # Obuna hali faol — login/parol har doim qayta ko'rsatiladi (xavfsizlik uchun)
        await send_active_subscription_info(message, user)
        return

    # Obuna tugagan yoki hali to'lov qilinmagan — to'lov taklifi ko'rsatiladi
    await send_welcome_offer(message, user.language, message.from_user.full_name)


@router.message(Command("language"))
async def cmd_language(message: Message):
    user = await get_user(message.from_user.id)
    language = user.language if user else "uz"
    await message.answer(
        t(language, "choose_language"),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery):
    language = callback.data.split(":", 1)[1]  # uz | ru | en

    existing_user = await get_user(callback.from_user.id)
    is_first_time = not (existing_user and existing_user.language_selected)

    await set_language(callback.from_user.id, language)
    await callback.message.edit_text(t(language, "language_set"))

    if is_first_time:
        # Faqat botga birinchi marta kirganda qo'llanma video yuboriladi
        await send_tutorial_video(callback.message, language)

    user = await get_user(callback.from_user.id)
    if user and user.is_paid:
        await send_active_subscription_info(callback.message, user)
    else:
        await send_welcome_offer(
            callback.message, language, callback.from_user.full_name
        )

    await callback.answer()
