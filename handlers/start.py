import os
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatType

from config import config
from database.requests import (
    get_or_create_user,
    set_language,
    get_user,
    get_user_by_group_chat_id,
)
from locales.texts import t
from utils.keyboards import pay_keyboard, reports_keyboard
from utils.credentials import decrypt_password

router = Router(name="start")
logger = logging.getLogger(__name__)

LANG = "uz"  # Bot faqat o'zbekcha


async def send_welcome_offer(message: Message, name: str) -> None:
    await message.answer(
        t(
            LANG,
            "welcome_offer",
            name=name,
            price=f"{config.product_price:,}".replace(",", " "),
        ),
        reply_markup=pay_keyboard(),
    )


async def send_active_subscription_info(message: Message, user) -> None:
    """Obuna faol bo'lganda login/parolni ko'rsatadi va hisobot tugmalarini chiqaradi."""
    password = decrypt_password(user.site_password_encrypted)
    await message.answer(
        t(
            LANG,
            "already_paid",
            website=config.website_url,
            login=user.site_login,
            password=password,
        ),
        reply_markup=reports_keyboard(),
    )


async def send_tutorial_video(message: Message) -> None:
    """Birinchi marta /start bosilganda qo'llanma videosini yuboradi."""
    if not config.video_path or not os.path.exists(config.video_path):
        logger.warning("Qo'llanma video fayli topilmadi: %s", config.video_path)
        return
    try:
        video = FSInputFile(config.video_path)
        await message.answer_video(video, caption=t(LANG, "tutorial_caption"))
    except Exception:
        logger.exception("Video yuborishda xatolik")


@router.message(CommandStart(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def cmd_start_in_group(message: Message):
    """Guruhda /start — faqat bog'lanish holati."""
    linked_user = await get_user_by_group_chat_id(message.chat.id)

    if linked_user:
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
async def cmd_start(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    # Til tanlash yo'q — doim o'zbekcha
    is_first_time = not user.language_selected
    if is_first_time:
        await set_language(message.from_user.id, LANG)
        await send_tutorial_video(message)

    # Yangilangan user
    user = await get_user(message.from_user.id)

    if user and user.is_paid:
        await send_active_subscription_info(message, user)
        return

    await send_welcome_offer(message, message.from_user.full_name)
