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

- ✅ /start → til tanlash (uz/ru/en) → shu tilda muloqot
- ✅ To'lov taklifi va to'lov usulini tanlash (Click/Payme/Boshqa)
- ✅ Har bir foydalanuvchi uchun **unikal, bazada takrorlanmaydigan** login va kuchli parol generatsiyasi (parol bazada faqat bcrypt xesh ko'rinishida saqlanadi)
- ✅ To'lovdan keyin veb-sayt linki + login/parol yuboriladi
- ⚠️ **To'lov hozircha `mock` (demo) rejimda** — haqiqiy pul o'tkazilmaydi, faqat oqim sinaladi. `.env` da `PAYMENT_MODE=mock`

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
