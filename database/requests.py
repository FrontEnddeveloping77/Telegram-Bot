from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from config import config
from database.engine import async_session
from database.models import User, Notification


async def get_or_create_user(
    telegram_id: int, full_name: str, username: str | None
) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def set_language(telegram_id: int, language: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.language = language
            user.language_selected = True
            await session.commit()


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def renew_or_activate_subscription(
    telegram_id: int,
    payment_method: str,
    payment_id: str,
    new_login: str,
    new_password_encrypted: str,
    new_password_hash: str,
) -> tuple[str, str]:
    """
    To'lovdan keyin (birinchi marta yoki qayta) obunani faollashtiradi.
    Login VA parol: FAQAT birinchi to'lovda yaratiladi. Keyingi barcha to'lovlarda
    (obuna qayta faollashtirilganda) ESKI login va ESKI parol o'zgarmasdan qaytariladi —
    chunki veb-saytda shu login/parol orqali saqlangan ma'lumotlar bog'liq bo'ladi.

    Qaytaradi: (login, shifrlangan_parol)
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=config.subscription_duration_minutes)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Foydalanuvchi topilmadi")

        if user.site_login is None:
            user.site_login = new_login
            user.site_password_encrypted = new_password_encrypted
            user.site_password_hash = new_password_hash

        user.is_paid = True
        user.payment_method = payment_method
        user.payment_id = payment_id
        user.paid_at = now
        user.expires_at = expires_at

        await session.commit()
        return user.site_login, user.site_password_encrypted


async def login_exists(site_login: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.site_login == site_login)
        )
        return result.scalar_one_or_none() is not None


async def get_users_with_expired_subscription() -> list[User]:
    """is_paid=True bo'lgan, lekin muddati o'tib ketgan userlarni qaytaradi (bildirishnoma yuborish uchun)."""
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_paid == True, User.expires_at <= now)  # noqa: E712
        )
        return list(result.scalars().all())


async def expire_subscription(telegram_id: int) -> None:
    """Obunani nofaol qiladi (login/parol bazada saqlanib qoladi, faqat is_paid=False bo'ladi)."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_paid = False
            await session.commit()


async def get_user_by_login(site_login: str) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.site_login == site_login)
        )
        return result.scalar_one_or_none()

async def get_user_by_group_chat_id(chat_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.linked_group_chat_id == chat_id)
        )
        return result.scalar_one_or_none()


async def link_group_to_user(site_login: str, chat_id: int) -> None:
    """Berilgan login egasi userga shu guruh (chat_id) ni bog'laydi."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.site_login == site_login)
        )
        user = result.scalar_one_or_none()
        if user:
            user.linked_group_chat_id = chat_id
            await session.commit()


async def get_pending_notifications() -> list[Notification]:
    """Hali yuborilmagan (is_sent=False) barcha bildirishnomalarni qaytaradi."""
    async with async_session() as session:
        result = await session.execute(
            select(Notification).where(Notification.is_sent == False)  # noqa: E712
        )
        return list(result.scalars().all())


async def mark_notification_sent(notification_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_sent = True
            await session.commit()
