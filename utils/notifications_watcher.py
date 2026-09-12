import asyncio
import base64
import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile
from utils.keyboards import app_links_keyboard

from database.requests import (
    get_pending_notifications,
    mark_notification_sent,
    get_user_by_login,
    get_linked_group_chat_ids,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 10


async def _send_notification(
    bot: Bot,
    chat_id: int,
    message: str,
    photo_url: str | None,
) -> None:
    text = str(message or "")
    photo_url = str(photo_url or "").strip()

    # ==================================================
    # RASM BILAN YUBORISH
    # ==================================================

    if photo_url:
        try:
            photo = None

            if photo_url.startswith("data:image"):
                parts = photo_url.split(",", 1)

                if len(parts) == 2:
                    raw = base64.b64decode(parts[1])
                    # Telegram limitiga yaqin bo'lsa ham fayl sifatida yuboramiz
                    photo = BufferedInputFile(raw, filename="product.jpg")

            elif photo_url.startswith("http://") or photo_url.startswith("https://"):
                # Avval URL; ishlamasa quyida download fallback
                photo = photo_url

            if photo is not None:
                caption = text[:1024] if text else None

                try:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=app_links_keyboard(),
                    )
                except Exception as url_err:
                    # http URL Telegram tomonidan ochilmasa — o'zimiz yuklab yuboramiz
                    if isinstance(photo, str) and photo.startswith("http"):
                        logger.warning(
                            "[NOTIFICATION] URL orqali rasm yuborilmadi, "
                            "yuklab qayta uriniladi: chat_id=%s err=%s",
                            chat_id,
                            url_err,
                        )
                        import asyncio
                        from urllib.request import urlopen, Request

                        def _download(url: str) -> bytes:
                            req = Request(
                                url, headers={"User-Agent": "TelegramBot/1.0"}
                            )
                            with urlopen(req, timeout=20) as resp:
                                return resp.read()

                        data = await asyncio.to_thread(_download, photo)
                        photo_file = BufferedInputFile(data, filename="product.jpg")
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=photo_file,
                            caption=caption,
                            parse_mode="HTML",
                            reply_markup=app_links_keyboard(),
                        )
                    else:
                        raise

                if len(text) > 1024:
                    remaining = text[1024:]

                    for i in range(0, len(remaining), 4096):
                        await bot.send_message(
                            chat_id=chat_id,
                            text=remaining[i : i + 4096],
                            parse_mode="HTML",
                            reply_markup=app_links_keyboard(),
                        )

                return

        except Exception as error:
            logger.exception(
                "[NOTIFICATION] Rasm yuborilmadi. "
                "Matn sifatida qayta yuboriladi. "
                "chat_id=%s error=%s",
                chat_id,
                error,
            )

    # ==================================================
    # FAQAT MATN
    # ==================================================

    if not text:
        text = "🔔 Yangi bildirishnoma"

    for i in range(0, len(text), 4096):
        await bot.send_message(
            chat_id=chat_id,
            text=text[i : i + 4096],
            parse_mode="HTML",
            reply_markup=app_links_keyboard(),
        )


async def notifications_watcher(bot: Bot) -> None:
    logger.info("🚀 Telegram notification watcher ishga tushdi")

    while True:
        try:
            notifications = await get_pending_notifications()

            if notifications:
                logger.info(
                    "🔔 Yuborilmagan notificationlar: %s ta",
                    len(notifications),
                )

            for notification in notifications:
                notification_id = notification.id
                site_login = notification.site_login

                logger.info(
                    "[NOTIFICATION] id=%s login=%s",
                    notification_id,
                    site_login,
                )

                # ==================================================
                # USERNI TOPISH
                # ==================================================

                user = await get_user_by_login(site_login)

                if not user:
                    logger.error(
                        "[NOTIFICATION] User topilmadi: login=%s",
                        site_login,
                    )

                    continue

                # ==================================================
                # GURUHLARNI TOPISH
                # ==================================================

                chat_ids = await get_linked_group_chat_ids(user)

                if not chat_ids:
                    logger.error(
                        "[NOTIFICATION] " "Bu login uchun bog'langan guruh yo'q: %s",
                        site_login,
                    )

                    continue

                logger.info(
                    "[NOTIFICATION] login=%s → %s ta guruh topildi: %s",
                    site_login,
                    len(chat_ids),
                    chat_ids,
                )

                # ==================================================
                # HAR BIR GURUHGA YUBORISH
                # ==================================================

                any_sent = False

                for chat_id in chat_ids:
                    try:
                        await _send_notification(
                            bot=bot,
                            chat_id=int(chat_id),
                            message=notification.message,
                            photo_url=getattr(
                                notification,
                                "photo_url",
                                None,
                            ),
                        )

                        any_sent = True

                        logger.info(
                            "✅ NOTIFICATION YUBORILDI: " "id=%s chat_id=%s login=%s",
                            notification_id,
                            chat_id,
                            site_login,
                        )

                    except Exception as error:
                        logger.exception(
                            "❌ Guruhga yuborilmadi: "
                            "id=%s chat_id=%s login=%s error=%s",
                            notification_id,
                            chat_id,
                            site_login,
                            error,
                        )

                # ==================================================
                # MUVAFFAQIYATLI BO'LSA SENT QILISH
                # ==================================================

                if any_sent:
                    try:
                        await mark_notification_sent(notification_id)

                        logger.info(
                            "✅ Notification is_sent=true: id=%s",
                            notification_id,
                        )

                    except Exception as error:
                        logger.exception(
                            "❌ is_sent=true qilishda xato: id=%s error=%s",
                            notification_id,
                            error,
                        )

                else:
                    logger.warning(
                        "⚠️ Notification hech qaysi guruhga " "yuborilmadi: id=%s",
                        notification_id,
                    )

        except Exception as error:
            logger.exception(
                "❌ Notification watcher umumiy xatosi: %s",
                error,
            )

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
