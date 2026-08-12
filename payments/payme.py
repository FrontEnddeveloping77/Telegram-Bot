"""
Payme Merchant API integratsiyasi.

Merchant hisob olingandan so'ng (https://business.payme.uz) shu yerga
Payme to'lov havolasini generatsiya qilish kodi yoziladi. Payme ham
CheckPerformTransaction/CreateTransaction/PerformTransaction so'rovlarini
sizning serveringizga yuboradi — bular uchun alohida webhook endpoint kerak.

Hozircha bu funksiya faqat skelet — real integratsiya keyingi bosqichda qo'shiladi.
"""

from config import config


async def charge_via_payme(telegram_id: int) -> tuple[bool, str]:
    if not config.payme_merchant_id or not config.payme_key:
        raise RuntimeError("PAYME sozlamalari .env faylida to'ldirilmagan")

    # TODO: Payme to'lov havolasini yaratish (checkout.payme.uz/{merchant_id}?...)
    # va Payme webhook orqali kelgan PerformTransaction'da is_paid=True qilish
    raise NotImplementedError("Payme integratsiyasi hali ulanmagan")
