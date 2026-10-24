import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from database.requests import (
    delete_expired_user,
    expire_subscription,
    get_users_with_expired_subscription,
    save_reminder_state,
)
from locales.texts import t
from utils.keyboards import pay_keyboard

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60
REMINDER_HOUR = 10
LOCAL_TIMEZONE = timezone(timedelta(hours=5), "Asia/Tashkent")
FINAL_WARNING_DAYS = 3
PAID_GRACE_DAYS = 10


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _deletion_deadline(expires_at: datetime, payment_method: str | None) -> datetime:
    grace_days = 0 if payment_method == "trial" else PAID_GRACE_DAYS
    return expires_at + timedelta(days=grace_days + FINAL_WARNING_DAYS)


async def subscription_expiry_watcher(bot: Bot) -> None:
    """Har kuni Toshkent vaqti bilan eslatadi va belgilangan muddatda akkauntni o'chiradi."""
    while True:
        now = datetime.now(timezone.utc)
        local_now = now.astimezone(LOCAL_TIMEZONE)

        if local_now.hour >= REMINDER_HOUR:
            try:
                expired_users = await get_users_with_expired_subscription()
                for user in expired_users:
                    expires_at = _as_utc(user.expires_at)
                    last_reminder = (
                        _as_utc(user.last_reminder_at)
                        if user.last_reminder_at
                        else None
                    )
                    if last_reminder and last_reminder.astimezone(LOCAL_TIMEZONE).date() >= local_now.date():
                        continue

                    if user.is_paid:
                        await expire_subscription(user.telegram_id)

                    deletion_at = _deletion_deadline(expires_at, user.payment_method)
                    last_warning = (
                        _as_utc(user.last_deletion_warning_at)
                        if user.last_deletion_warning_at
                        else None
                    )
                    last_warning_date = (
                        last_warning.astimezone(LOCAL_TIMEZONE).date()
                        if last_warning
                        else None
                    )

                    if (
                        now >= deletion_at
                        and user.deletion_warning_count >= FINAL_WARNING_DAYS
                        and last_warning_date is not None
                        and last_warning_date < local_now.date()
                    ):
                        await delete_expired_user(user.telegram_id)
                        logger.info("Muddati o'tgan akkaunt o'chirildi: %s", user.telegram_id)
                        continue

                    warning_window_start = deletion_at - timedelta(days=FINAL_WARNING_DAYS)
                    if now >= warning_window_start:
                        previous_count = user.deletion_warning_count
                        if last_warning_date != local_now.date() - timedelta(days=1):
                            previous_count = 0
                        warning_count = previous_count + 1
                        message = t(user.language or "uz", "deletion_warning")
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                message,
                                reply_markup=pay_keyboard(),
                            )
                        except Exception:
                            logger.exception(
                                "Yakuniy ogohlantirish yuborilmadi: %s",
                                user.telegram_id,
                            )
                            await save_reminder_state(user.telegram_id, now)
                            continue
                        await save_reminder_state(
                            user.telegram_id,
                            now,
                            deletion_warning_count=warning_count,
                            last_deletion_warning_at=now,
                        )
                    else:
                        message_key = (
                            "subscription_expired"
                            if expires_at.astimezone(LOCAL_TIMEZONE).date() == local_now.date()
                            else "payment_reminder"
                        )
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                t(user.language or "uz", message_key),
                                reply_markup=pay_keyboard(),
                            )
                        except Exception:
                            logger.exception(
                                "To'lov eslatmasi yuborilmadi: %s",
                                user.telegram_id,
                            )
                            await save_reminder_state(user.telegram_id, now)
                            continue
                        await save_reminder_state(user.telegram_id, now)
            except Exception:
                logger.exception("Obuna eslatmalarini tekshirishda xatolik")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)