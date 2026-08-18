import asyncio
import logging

from aiogram import Bot

from database.requests import get_users_with_expired_subscription, expire_subscription
from locales.texts import t
from utils.keyboards import pay_keyboard

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 15  # obunalarni har necha soniyada 


async def subscription_expiry_watcher(bot: Bot) -> None:
    """
    Doimiy ishlaydigan fon vazifa: muddati tugagan obunalarni topadi,
    userga xabar yuboradi (to'lov tugmasi bilan) va bazada is_paid=False qilib qo'yadi.
    """
    while True:
        try:
            expired_users = await get_users_with_expired_subscription()
            for user in expired_users:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        t(user.language, "subscription_expired"),
                        reply_markup=pay_keyboard(),
                    )
                except Exception:
                    logger.exception(
                        "Foydalanuvchiga xabar yuborib bo'lmadi: %s", user.telegram_id
                    )
                finally:
                    await expire_subscription(user.telegram_id)
        except Exception:
            logger.exception("Obunalarni tekshirishda xatolik")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
