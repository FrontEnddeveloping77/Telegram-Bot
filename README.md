# Telegram to'lov boti

## Ishga tushirish

1. Python 3.11+ o'rnatilgan bo'lishi kerak
2. Virtual muhit yaratish:
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. PostgreSQL o'rnating va bo'sh baza yarating (masalan `mybot_db`)
4. `.env.example` faylidan nusxa oling:
   ```
   cp .env.example .env
   ```
   va quyidagilarni to'ldiring:
   - `BOT_TOKEN` — @BotFather'dan olinadi
   - `DATABASE_URL` — PostgreSQL manzilingiz
   - `PRODUCT_PRICE`, `WEBSITE_URL`
5. Botni ishga tushiring:
   ```
   python main.py
   ```

Birinchi ishga tushirishda kerakli jadvallar avtomatik yaratiladi.

## Hozirgi holat

- ✅ `/start` do'kondagi turli tovarlar sonini so'raydi va ikkita tarifni taklif qiladi.
- ✅ Foyda tarifi: oylik sof foydaning 15%; tovar tarifi: har 100 xil ID uchun 50 000 so'm.
- ✅ Tarif tanlanganda bir marta 3 kunlik sinov va shaxsiy login/parol beriladi.
- ✅ To'lov summasi tanlangan tarif bo'yicha hisoblanadi; foyda tarifi hisobot API'sidagi oylik sof foydadan olinadi.
- ✅ Muddati tugagan akkauntga har kuni Toshkent vaqti bilan soat 10:00 dan keyin eslatma yuboriladi. Ikki kalendar oydan keyin uch kun ketma-ket ogohlantirish berilib, so'ng akkaunt va bot bazasidagi bog'liq ma'lumotlar o'chiriladi.
- ✅ Sotuv notification'i har bir bog'langan guruhga alohida qayd qilinadi, qayta urinishda avval olgan guruhga takror yuborilmaydi.
- ✅ Bot xabarlarida sayt yoki APK havolasi chiqarilmaydi. `WEBSITE_URL` faqat hisobot API manzilini aniqlash uchun ishlatiladi.
- ⚠️ Karta cheklari admin tomonidan qo'lda ko'rib chiqiladi; Click/Payme webhook integratsiyasi alohida sozlanmagan.

## Click/Payme ni real ulash

Merchant hisob (https://merchant.click.uz va https://business.payme.uz) tayyor bo'lgach:

1. `.env` dagi `CLICK_*` va `PAYME_*` qiymatlarini to'ldiring, `PAYMENT_MODE=real` qiling
2. `payments/click.py` va `payments/payme.py` fayllaridagi `TODO` qismlarini to'ldiramiz
3. Click/Payme sizning serveringizga webhook (PREPARE/COMPLETE va CheckPerformTransaction/PerformTransaction) yuboradi — bular uchun bot jarayonidan tashqarida alohida veb-server (masalan FastAPI) kerak bo'ladi. Buni birga sozlaymiz.

## Fayl tuzilishi

```
telegram_bot/
├── main.py                 # Ishga tushirish nuqtasi
├── config.py                # .env dan sozlamalarni o'qish
├── handlers/
│   ├── start.py             # /start, til tanlash
│   └── payment.py           # To'lov oqimi
├── database/
│   ├── models.py            # User modeli
│   ├── engine.py            # DB ulanish
│   └── requests.py          # CRUD funksiyalari
├── locales/
│   └── texts.py             # uz/ru/en matnlar
├── payments/
│   ├── processor.py         # mock/real rejim tanlovchi
│   ├── click.py              # Click integratsiyasi (skelet)
│   └── payme.py              # Payme integratsiyasi (skelet)
└── utils/
    ├── keyboards.py          # Inline klaviaturalar
    └── credentials.py        # Login/parol generatori
```
