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

- ✅ `/start` do'kondagi tovarlar soni (ID) va ulanadigan guruhlar soni bo'yicha qat'iy tariflarni taklif qiladi.
- ✅ Tariflar: 1 000, 2 000, 3 000, 4 000, 5 000 tagacha ID; 1 ta, 2 ta va 3-5 ta guruh variantlari mavjud.
- ✅ 5 000 tadan ko'p tovar yoki 5 tadan ko'p guruh uchun to'g'ridan-to'g'ri admin (@ABDULAZIZ_AVAZOV) ga murojaat qilinadi.
- ✅ Guruh limiti bot tomonidan avtomatik nazorat qilinadi.
- ✅ Yangi foydalanuvchi tarif tanlagach 7 kunlik bepul sinovni boshlashi mumkin.
- ✅ Akkaunt sozlanayotganda tovarlar uchun qaytarish (vozvrat) siyosati so'ralib, foydalanuvchi tanlovi saqlanadi. Sayt backendida ushbu sozlamani ijro etish alohida integratsiyani talab qiladi.
- ✅ Bepul sinov tugagach 3 kun ketma-ket, Toshkent vaqti bilan soat 10:00 da ogohlantirish yuboriladi va keyin akkaunt o'chiriladi. Pulli obuna muddati tugagach 10 kundan so'ng 3 kunlik ogohlantirish boshlanadi; so'ng akkaunt va bot bazasidagi bog'liq ma'lumotlar o'chiriladi.
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
