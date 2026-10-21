import asyncio
import base64
import json
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile

from database.requests import (
    get_pending_notifications,
    mark_notification_chat_sent,
    get_user_by_login,
    get_linked_group_chat_ids,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 10


def _normalize_meta_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _extract_product_meta(message: str | None, product_id: str | None, product_category: str | None):
    payload = {}
    text = str(message or "").strip()

    if text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                payload = parsed
        except (TypeError, ValueError):
            pass

    product_id = _normalize_meta_value(product_id)
    product_category = _normalize_meta_value(product_category)

    if product_id is None:
        product_id = (
            payload.get("product_id")
            or payload.get("productId")
            or payload.get("productID")
            or payload.get("id")
            or payload.get("item_id")
            or payload.get("itemId")
        )
    if product_category is None:
        product_category = (
            payload.get("product_category")
            or payload.get("category")
            or payload.get("productCategory")
            or payload.get("type")
        )

    return {
        "product_id": _normalize_meta_value(product_id),
        "product_category": _normalize_meta_value(product_category),
    }


async def _send_notification(
    bot: Bot,
    chat_id: int,
    message: str,
    photo_url: str | None,
    product_id: str | None = None,
    product_category: str | None = None,
) -> None:
    text = str(message or "")
    photo_url = str(photo_url or "").strip()
    meta = _extract_product_meta(text, product_id, product_category)

    if meta["product_id"] or meta["product_category"]:
        lines = [text.strip() if text.strip() else "🔔 Yangi bildirishnoma"]
        if meta["product_id"]:
            lines.append(f"📦 <b>Tovar ID:</b> {meta['product_id']}")
        if meta["product_category"]:
            lines.append(f"🏷 <b>Kategoriya:</b> {meta['product_category']}")
        text = "\n".join(lines)

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
                    )
                except TelegramBadRequest as url_err:
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
                        )

                return

        except TelegramBadRequest as error:
            logger.exception(
                "[NOTIFICATION] Rasm yuborilmadi. "
                "Matn sifatida qayta yuboriladi. "
                "chat_id=%s error=%s",
                chat_id,
                error,
            )
        except Exception:
            logger.exception(
                "[NOTIFICATION] Rasm yuborishda noaniq xatolik; "
                "matnli nusxa yuborilmaydi: chat_id=%s",
                chat_id,
            )
            raise

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
                val = getattr(notification, "delivered_chat_ids", [])
                if isinstance(val, list):
                    delivered_chat_ids = {int(v) for v in val}
                elif isinstance(val, str):
                    try:
                        delivered_chat_ids = {int(v) for v in json.loads(val or "[]")}
                    except (TypeError, ValueError):
                        delivered_chat_ids = set()
                else:
                    delivered_chat_ids = set()

                for chat_id in chat_ids:
                    if int(chat_id) in delivered_chat_ids:
                        continue
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
                            product_id=getattr(notification, "product_id", None),
                            product_category=getattr(
                                notification,
                                "product_category",
                                None,
                            ),
                        )

                        any_sent = True
                        await mark_notification_chat_sent(
                            notification_id,
                            int(chat_id),
                            [int(value) for value in chat_ids],
                        )
                        delivered_chat_ids.add(int(chat_id))

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

                if any_sent:
                    logger.info(
                        "✅ Guruhlar kesimida yetkazish qayd etildi: id=%s",
                        notification_id,
                    )
                elif not set(map(int, chat_ids)).issubset(delivered_chat_ids):
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
