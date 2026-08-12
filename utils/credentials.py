import secrets
import string
import bcrypt
from cryptography.fernet import Fernet

from config import config
from database.requests import login_exists

_LOGIN_PREFIX = "user"
_LOGIN_DIGITS = 6

_PASSWORD_LENGTH = 12
_PASSWORD_ALPHABET = string.ascii_letters + string.digits

_fernet = Fernet(config.fernet_key.encode()) if config.fernet_key else None


async def generate_unique_login() -> str:
    """Bazada mavjud bo'lmagan yagona login yaratadi, masalan: user482913"""
    while True:
        suffix = "".join(secrets.choice(string.digits) for _ in range(_LOGIN_DIGITS))
        candidate = f"{_LOGIN_PREFIX}{suffix}"
        if not await login_exists(candidate):
            return candidate


def generate_strong_password(length: int = _PASSWORD_LENGTH) -> str:
    """Faqat harflar va raqamlardan iborat parol yaratadi (saytda muammosiz qabul qilinishi uchun)."""
    while True:
        password = "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password


def _require_fernet() -> Fernet:
    if _fernet is None:
        raise RuntimeError(
            "FERNET_KEY .env faylida ko'rsatilmagan. Uni yaratish uchun terminalda yozing:\n"
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return _fernet


def encrypt_password(plain_password: str) -> str:
    """Parolni qaytarib ochish mumkin bo'lgan holda shifrlaydi (bazada shu holda saqlanadi)."""
    return _require_fernet().encrypt(plain_password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    """Bazada saqlangan shifrlangan parolni asl (ochiq) ko'rinishga qaytaradi."""
    return _require_fernet().decrypt(encrypted_password.encode()).decode()


def hash_password_for_site(plain_password: str) -> str:
    """
    Veb-sayt login tekshiruvi uchun bcrypt xesh yaratadi (qaytarib bo'lmaydi).
    Node.js'dagi bcryptjs kutubxonasi bilan to'liq mos keladi.
    """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
