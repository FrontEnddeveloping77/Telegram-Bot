"""
To'lovlarni qayta ishlash moduli.

Hozircha PAYMENT_MODE=mock rejimida ishlaydi — haqiqiy Click/Payme so'rovi
yuborilmaydi, to'lov avtomatik "muvaffaqiyatli" deb hisoblanadi (test/demo uchun).

Merchant hisob (Click/Payme) tayyor bo'lgach:
1. .env faylida CLICK_* / PAYME_* qiymatlarini to'ldiring
2. PAYMENT_MODE=real qiling
3. payments/click.py va payments/payme.py fayllaridagi
   TODO qismlarini haqiqiy API chaqiruvlari bilan to'ldiring
   (Click Invoice/Merchant API, Payme Merchant API hujjatlariga asosan)
"""

import uuid
from config import config


async def process_payment(telegram_id: int, method: str) -> tuple[bool, str]:
    """
    To'lovni amalga oshiradi.
    Qaytaradi: (muvaffaqiyatli_boldimi, tashqi_tolov_id)
    """
    if config.payment_mode == "mock":
        # Demo rejim: to'lov har doim muvaffaqiyatli deb hisoblanadi
        fake_payment_id = f"MOCK-{method.upper()}-{uuid.uuid4().hex[:10]}"
        return True, fake_payment_id

    if method == "click":
        from payments.click import charge_via_click
        return await charge_via_click(telegram_id)

    if method == "payme":
        from payments.payme import charge_via_payme
        return await charge_via_payme(telegram_id)

    return False, ""
