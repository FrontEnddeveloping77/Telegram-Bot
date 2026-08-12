import asyncio
import logging

from aiogram import Bot

from database.requests import (
    get_pending_notifications,
    mark_notification_sent,
    get_user_by_login,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 10  # bildirishnomalarni har necha soniyada tekshirish


async def notifications_watcher(bot: Bot) -> None:
    """
    Doimiy ishlaydigan fon vazifa: veb-sayt tomonidan 'notifications' jadvaliga
    yozilgan yangi xabarlarni topadi va tegishli login egasining bog'langan
    guruhiga yuboradi.
    """
    while True:
        try:
            pending = await get_pending_notifications()
            for notification in pending:
                user = await get_user_by_login(notification.site_login)

                if not user or not user.linked_group_chat_id:
                    continue

                try:
                    await bot.send_message(
                        user.linked_group_chat_id, notification.message
                    )
                    await mark_notification_sent(notification.id)
                except Exception:
                    logger.exception(
                        "Guruhga bildirishnoma yuborib bo'lmadi: chat_id=%s",
                        user.linked_group_chat_id,
                    )
        except Exception:
            logger.exception("Bildirishnomalarni tekshirishda xatolik")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
