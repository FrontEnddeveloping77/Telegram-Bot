from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)

    # "uz" | "ru" | "en"
    language: Mapped[str] = mapped_column(String(2), default="uz")
    language_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=True
    )  # click | payme
    payment_id: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # tashqi tizim tranzaksiya ID
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Veb-saytga kirish uchun generatsiya qilingan login/parol
    site_login: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    # Botda qayta ko'rsatish uchun (qaytarib ochiladigan shifrlash, Fernet)
    site_password_encrypted: Mapped[str] = mapped_column(String(255), nullable=True)
    # Veb-sayt tomonidan login tekshirish uchun (qaytarib bo'lmaydigan xesh, bcrypt)
    site_password_hash: Mapped[str] = mapped_column(String(255), nullable=True)

    # Ushbu userning login/paroli tasdiqlangan Telegram guruhi (bildirishnomalar shu yerga yuboriladi)
    linked_group_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Notification(Base):
    """
    Veb-sayt tomonidan yozib qo'yiladigan bildirishnomalar (masalan: 'mahsulot qo'shildi').
    Bot bu jadvalni davriy tekshirib, tegishli guruhga yuboradi.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_login: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
