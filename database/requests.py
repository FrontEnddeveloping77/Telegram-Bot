import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from config import config
from database.engine import async_session
from database.models import User, Notification, PaymentRequest


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


# ===================== To'lov cheklari (karta orqali qo'lda to'lov) =====================


async def create_payment_request(
    telegram_id: int, receipt_file_id: str
) -> PaymentRequest:
    async with async_session() as session:
        payment_request = PaymentRequest(
            telegram_id=telegram_id,
            receipt_file_id=receipt_file_id,
            status="pending",
        )
        session.add(payment_request)
        await session.commit()
        await session.refresh(payment_request)
        return payment_request


async def get_payment_request(request_id: int) -> PaymentRequest | None:
    async with async_session() as session:
        result = await session.execute(
            select(PaymentRequest).where(PaymentRequest.id == request_id)
        )
        return result.scalar_one_or_none()


async def set_payment_request_admin_messages(
    request_id: int, admin_message_ids: dict[int, int]
) -> None:
    """admin_message_ids: {admin_telegram_id: message_id, ...}"""
    async with async_session() as session:
        result = await session.execute(
            select(PaymentRequest).where(PaymentRequest.id == request_id)
        )
        payment_request = result.scalar_one_or_none()
        if payment_request:
            payment_request.admin_message_ids = json.dumps(
                {str(k): v for k, v in admin_message_ids.items()}
            )
            await session.commit()


async def claim_payment_request(
    request_id: int, admin_id: int, new_status: str, from_status: str = "pending"
) -> PaymentRequest | None:
    """
    Berilgan to'lov so'rovini FAQAT hozirgi holati `from_status` bo'lsa,
    `new_status`ga o'tkazadi va shu adminni biriktiradi (atomik amal —
    bir nechta admin bir vaqtda bosishi natijasida ikki marta ishlanib
    ketmasligi uchun).

    Qaytaradi: yangilangan PaymentRequest (agar amal muvaffaqiyatli bo'lsa),
    aks holda None (bu so'rov allaqachon boshqa admin tomonidan ko'rib chiqilgan).
    """
    async with async_session() as session:
        result = await session.execute(
            update(PaymentRequest)
            .where(
                PaymentRequest.id == request_id, PaymentRequest.status == from_status
            )
            .values(status=new_status, admin_id=admin_id)
        )
        await session.commit()
        if result.rowcount == 0:
            return None

        refreshed = await session.execute(
            select(PaymentRequest).where(PaymentRequest.id == request_id)
        )
        return refreshed.scalar_one_or_none()


async def finalize_payment_rejection(request_id: int, reject_reason: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PaymentRequest).where(PaymentRequest.id == request_id)
        )
        payment_request = result.scalar_one_or_none()
        if payment_request:
            payment_request.status = "rejected"
            payment_request.reject_reason = reject_reason
            payment_request.decided_at = datetime.now(timezone.utc)
            await session.commit()


async def finalize_payment_approval(request_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PaymentRequest).where(PaymentRequest.id == request_id)
        )
        payment_request = result.scalar_one_or_none()
        if payment_request:
            payment_request.decided_at = datetime.now(timezone.utc)
            await session.commit()
