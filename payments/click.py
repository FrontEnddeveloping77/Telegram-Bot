"""
Click Merchant API integratsiyasi.

Merchant hisob olingandan so'ng (https://merchant.click.uz) shu yerga
Click Invoice API chaqiruvini yozamiz: to'lov havolasi/invoys yaratish,
so'ngra Click tomonidan yuboriladigan webhook (PREPARE/COMPLETE so'rovlari)
uchun alohida FastAPI/aiohttp endpoint kerak bo'ladi (bot ichida emas,
chunki Click sizning serveringizga HTTP so'rov yuboradi).

Hozircha bu funksiya faqat skelet — real integratsiya keyingi bosqichda qo'shiladi.
"""

from config import config


async def charge_via_click(telegram_id: int) -> tuple[bool, str]:
    if not config.click_service_id or not config.click_secret_key:
        raise RuntimeError("CLICK sozlamalari .env faylida to'ldirilmagan")

    # TODO: Click Invoice API chaqiruvi shu yerga yoziladi
    # 1. Invoice yaratish (POST /invoice/create)
    # 2. Foydalanuvchiga to'lov havolasini yuborish
    # 3. Click webhook orqali PREPARE/COMPLETE kelganda bazada is_paid=True qilish
    raise NotImplementedError("Click integratsiyasi hali ulanmagan")
