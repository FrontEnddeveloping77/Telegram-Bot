import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    admin_ids: list[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
        ]
    )
    product_price: int = int(os.getenv("PRODUCT_PRICE", "0"))
    website_url: str = os.getenv("WEBSITE_URL", "")

    # Obuna necha daqiqa amal qiladi (test uchun 5, productionda masalan 43200 = 30 kun)
    subscription_duration_minutes: int = int(
        os.getenv("SUBSCRIPTION_DURATION_MINUTES", "5")
    )

    # Parolni shifrlash/qayta ochish uchun maxfiy kalit (Fernet.generate_key() bilan yaratiladi)
    fernet_key: str = os.getenv("FERNET_KEY", "")

    # Birinchi marta /start bosilganda yuboriladigan qo'llanma video fayli manzili
    video_path: str = os.getenv("VIDEO_PATH", "media/tutorial.mp4")

    click_service_id: str = os.getenv("CLICK_SERVICE_ID", "")
    click_merchant_id: str = os.getenv("CLICK_MERCHANT_ID", "")
    click_secret_key: str = os.getenv("CLICK_SECRET_KEY", "")

    payme_merchant_id: str = os.getenv("PAYME_MERCHANT_ID", "")
    payme_key: str = os.getenv("PAYME_KEY", "")

    payment_mode: str = os.getenv("PAYMENT_MODE", "mock")  # "mock" | "real"

    # Qo'lda (karta orqali) to'lov uchun ko'rsatiladigan karta ma'lumotlari
    card_number: str = os.getenv("CARD_NUMBER", "")
    card_holder_name: str = os.getenv("CARD_HOLDER_NAME", "")


config = Config()
