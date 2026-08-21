import asyncio
import base64
import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile

from database.requests import (
    get_pending_notifications,
    mark_notification_sent,
    get_user_by_login,
    get_linked_group_chat_ids,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 10  # bildirishnomalarni har necha soniyada tekshirish


async def _send_notification(
    bot: Bot, chat_id: int, message: str, photo_url: str | None
) -> None:
    """
    Rasm bo'lsa send_photo (caption), bo'lmasa send_message.
    Telegram caption limiti — 1024 belgi; uzun matn ikkinchi xabarda ketadi.
    """
    text = message or ""
    photo_url = (photo_url or "").strip()

    if photo_url:
        try:
            if photo_url.startswith("data:image"):
                # data:image/jpeg;base64,XXXX
                b64 = photo_url.split(",", 1)[1]
                raw = base64.b64decode(b64)
                photo = BufferedInputFile(raw, filename="product.jpg")
            elif photo_url.startswith("http://") or photo_url.startswith("https://"):
                photo = photo_url  # URL
            else:
                photo = None

            if photo is not None:
                caption = text[:1024] if text else None
                await bot.send_photo(
                    chat_id,
                    photo,
                    caption=caption,
                    parse_mode="HTML",
                )
                if len(text) > 1024:
                    await bot.send_message(chat_id, text[1024:], parse_mode="HTML")
                return
        except Exception:
            logger.exception(
                "Rasm yuborib bo'lmadi, matn sifatida yuboriladi: chat_id=%s", chat_id
            )

    # Rasm yo'q yoki rasm xato — oddiy matn
    if len(text) <= 4096:
        await bot.send_message(chat_id, text, parse_mode="HTML")
    else:
        for i in range(0, len(text), 4096):
            await bot.send_message(chat_id, text[i : i + 4096], parse_mode="HTML")


async def notifications_watcher(bot: Bot) -> None:
    """
    Doimiy ishlaydigan fon vazifa: veb-sayt tomonidan 'notifications' jadvaliga
    yozilgan yangi xabarlarni topadi va tegishli login egasining bog'langan
    guruhiga yuboradi (rasm bo'lsa — rasm + matn).
    """
    while True:
        try:
            pending = await get_pending_notifications()
            for notification in pending:
                user = await get_user_by_login(notification.site_login)

                if not user:
                    logger.debug(
                        "User yo'q: login=%s",
                        notification.site_login,
                    )
                    continue

                chat_ids = await get_linked_group_chat_ids(user)
                if not chat_ids:
                    logger.debug(
                        "Guruh bog'lanmagan: login=%s",
                        notification.site_login,
                    )
                    continue

                photo = getattr(notification, "photo_url", None)
                any_sent = False
                for chat_id in chat_ids:
                    try:
                        await _send_notification(
                            bot,
                            chat_id,
                            notification.message,
                            photo,
                        )
                        any_sent = True
                        logger.info(
                            "Bildirishnoma yuborildi: id=%s chat=%s photo=%s",
                            notification.id,
                            chat_id,
                            "YES" if photo else "NO",
                        )
                    except Exception:
                        logger.exception(
                            "Guruhga bildirishnoma yuborib bo'lmadi: chat_id=%s",
                            chat_id,
                        )
                if any_sent:
                    await mark_notification_sent(notification.id)
        except Exception:
            logger.exception("Bildirishnomalarni tekshirishda xatolik")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
