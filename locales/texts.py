TEXTS = {
    "uz": {
        "choose_language": "Tilni tanlang / Choose language / Выберите язык:",
        "language_set": "✅ Til o'zbekcha qilib o'rnatildi.",
        "welcome_offer": (
            "Assalomu alaykum, {name}!\n\n"
            "Xizmatdan foydalanish uchun to'lovni amalga oshiring. "
            "Narx: {price} so'm/oyiga.\n\n"
            "Pastdagi tugmani bosing 👇"
        ),
        "btn_pay": "💳 To'lov qilish",
        "card_payment_instructions": (
            "💳 To'lovni quyidagi karta orqali amalga oshiring:\n\n"
            "Karta raqami: <code>{card_number}</code>\n"
            "Karta egasi: <b>{card_holder}</b>\n"
            "Summa: <b>{price} so'm</b>\n\n"
            "1️⃣ Karta raqamini bosib nusxa oling (copy)\n"
            "2️⃣ Bankomat yoki istalgan mobil ilova orqali to'lovni amalga oshiring\n"
            "3️⃣ To'lov chekini (screenshot yoki rasm) shu yerga yuboring 👇"
        ),
        "receipt_invalid": "❗ Iltimos, to'lov chekini rasm (screenshot) shaklida yuboring.",
        "receipt_received": (
            "✅ Chekingiz qabul qilindi va admin tekshiruviga yuborildi.\n"
            "Tasdiqlangach sizga bu yerda xabar beramiz, biroz kuting."
        ),
        "payment_rejected_user": (
            "❌ Afsuski, to'lovingiz tasdiqlanmadi.\n\n"
            "Sabab: {reason}\n\n"
            "Iltimos, to'lovni qaytadan tekshirib, chekni qayta yuboring "
            "yoki savol bo'lsa admin bilan bog'laning."
        ),
        "admin_new_payment_request": (
            "🆕 Yangi to'lov cheki!\n\n"
            "👤 Foydalanuvchi: {full_name} (@{username})\n"
            "🆔 Telegram ID: <code>{telegram_id}</code>\n"
            "💰 Kutilayotgan summa: {price} so'm\n\n"
            "Chekni tekshirib, quyidagi tugmalardan birini tanlang 👇"
        ),
        "admin_already_handled": "⚠️ Bu to'lov so'rovi allaqachon ko'rib chiqilgan.",
        "admin_ask_reject_reason": (
            "❗ Rad etish sababini yozib yuboring — bu matn to'g'ridan-to'g'ri "
            "foydalanuvchiga yuboriladi.\n\n"
            'Masalan: "Chek noaniq, qaytadan yuboring" yoki "Summasi mos emas".'
        ),
        "admin_reject_reason_saved": "✅ Sabab qabul qilindi va foydalanuvchiga yuborildi.",
        "admin_approved_caption_suffix": "\n\n✅ <b>Tasdiqlandi</b> — {admin_name}",
        "admin_rejected_caption_suffix": "\n\n❌ <b>Rad etildi</b> — {admin_name}\nSabab: {reason}",
        "admin_pending_reason_caption_suffix": "\n\n⏳ {admin_name} rad etish sababini yozmoqda...",
        "processing_payment": "⏳ To'lov tekshirilmoqda, biroz kuting...",
        "payment_success": (
            "✅ To'lovingiz muvaffaqiyatli qabul qilindi!\n\n"
            "🌐 Veb-sayt: {website}\n\n"
            "🔑 Sizning shaxsiy kirish ma'lumotlaringiz:\n"
            "Login: <code>{login}</code>\n"
            "Parol: <code>{password}</code>\n\n"
            "⚠️ Bu ma'lumotlarni hech kimga bermang va saqlab qo'ying — qayta ko'rsatilmaydi."
        ),
        "payment_success_renewed": (
            "✅ To'lovingiz muvaffaqiyatli qabul qilindi!\n\n"
            "🔓 Login va parolingiz qayta faollashtirildi, endi saytga kirishingiz mumkin.\n"
            "🌐 Veb-sayt: {website}\n"
            "Login: <code>{login}</code>"
        ),
        "already_paid": (
            "Siz allaqachon to'lovni amalga oshirgansiz.\n\n"
            "🌐 Veb-sayt: {website}\n"
            "🔑 Login: <code>{login}</code>\n"
            "🔑 Parol: <code>{password}</code>"
        ),
        "subscription_expired": (
            "⏰ Sizning to'lov muddatingiz tugadi.\n\n"
            "Login va parolingiz vaqtincha ishlamay qoladi.\n"
            "Agar yana to'lov amalga oshirsangiz, login va parolingiz qayta ishlashni boshlaydi."
        ),
        "tutorial_caption": (
            "🎬 Botdan qanday foydalanish bo'yicha qisqacha video 👆\n\n"
            "✅ Botni to'liq ishlatish yo'riqnomasi shu videoda ko'rsatilgan\n"
            "📌 Savol tug'ilsa, video orqali qayta ko'rib chiqishingiz mumkin"
        ),
        "profit_daily": "📊 Bugungi sof foyda: {profit} so'm",
        "profit_weekly": "📊 Haftalik sof foyda: {profit} so'm",
        "profit_monthly": "📊 Oylik sof foyda: {profit} so'm",
        "profit_yearly": "📊 Yillik sof foyda: {profit} so'm",
        "profit_not_linked": "⚠️ Bu buyruq ishlashi uchun avval guruhni saytdagi hisobingizga bog'lashingiz kerak (login va parolni yuboring).",
        "profit_fetch_error": "❌ Ma'lumotni olishda xatolik yuz berdi. Birozdan keyin qayta urinib ko'ring.",
    },
    "ru": {
        "choose_language": "Tilni tanlang / Choose language / Выберите язык:",
        "language_set": "✅ Язык установлен на русский.",
        "welcome_offer": (
            "Здравствуйте, {name}!\n\n"
            "Чтобы воспользоваться сервисом, произведите оплату. "
            "Цена: {price} сум/в месяц.\n\n"
            "Нажмите кнопку ниже 👇"
        ),
        "btn_pay": "💳 Оплатить",
        "card_payment_instructions": (
            "💳 Произведите оплату на следующую карту:\n\n"
            "Номер карты: <code>{card_number}</code>\n"
            "Владелец карты: <b>{card_holder}</b>\n"
            "Сумма: <b>{price} сум</b>\n\n"
            "1️⃣ Нажмите на номер карты, чтобы скопировать его\n"
            "2️⃣ Оплатите через банкомат или любое мобильное приложение\n"
            "3️⃣ Отправьте сюда чек об оплате (скриншот или фото) 👇"
        ),
        "receipt_invalid": "❗ Пожалуйста, отправьте чек об оплате в виде изображения (скриншота).",
        "receipt_received": (
            "✅ Ваш чек принят и отправлен администратору на проверку.\n"
            "Как только он будет подтверждён, мы сообщим вам здесь, немного подождите."
        ),
        "payment_rejected_user": (
            "❌ К сожалению, ваш платёж не был подтверждён.\n\n"
            "Причина: {reason}\n\n"
            "Пожалуйста, проверьте платёж и отправьте чек заново, "
            "или свяжитесь с администратором."
        ),
        "admin_new_payment_request": (
            "🆕 Новый чек об оплате!\n\n"
            "👤 Пользователь: {full_name} (@{username})\n"
            "🆔 Telegram ID: <code>{telegram_id}</code>\n"
            "💰 Ожидаемая сумма: {price} сум\n\n"
            "Проверьте чек и выберите одно из действий ниже 👇"
        ),
        "admin_already_handled": "⚠️ Этот платёж уже был рассмотрен.",
        "admin_ask_reject_reason": (
            "❗ Напишите причину отклонения — этот текст будет отправлен "
            "пользователю напрямую.\n\n"
            "Например: «Чек нечёткий, отправьте заново» или «Сумма не совпадает»."
        ),
        "admin_reject_reason_saved": "✅ Причина сохранена и отправлена пользователю.",
        "admin_approved_caption_suffix": "\n\n✅ <b>Подтверждено</b> — {admin_name}",
        "admin_rejected_caption_suffix": "\n\n❌ <b>Отклонено</b> — {admin_name}\nПричина: {reason}",
        "admin_pending_reason_caption_suffix": "\n\n⏳ {admin_name} пишет причину отклонения...",
        "processing_payment": "⏳ Проверяем платёж, подождите...",
        "payment_success": (
            "✅ Оплата успешно принята!\n\n"
            "🌐 Сайт: {website}\n\n"
            "🔑 Ваши данные для входа:\n"
            "Логин: <code>{login}</code>\n"
            "Пароль: <code>{password}</code>\n\n"
            "⚠️ Никому не сообщайте эти данные и сохраните их — повторно они не будут показаны."
        ),
        "payment_success_renewed": (
            "✅ Оплата успешно принята!\n\n"
            "🔓 Ваш логин и пароль снова активированы, теперь вы можете войти на сайт.\n"
            "🌐 Сайт: {website}\n"
            "Логин: <code>{login}</code>"
        ),
        "already_paid": (
            "Вы уже произвели оплату.\n\n"
            "🌐 Сайт: {website}\n"
            "🔑 Логин: <code>{login}</code>\n"
            "🔑 Пароль: <code>{password}</code>"
        ),
        "subscription_expired": (
            "⏰ Срок вашей оплаты истёк.\n\n"
            "Ваш логин и пароль временно перестанут работать.\n"
            "Если вы произведёте оплату снова, ваш логин и пароль снова начнут работать."
        ),
        "tutorial_caption": (
            "🎬 Короткое видео о том, как пользоваться ботом 👆\n\n"
            "✅ Полная инструкция по использованию бота показана в этом видео\n"
            "📌 Если возникнут вопросы, можете пересмотреть видео"
        ),
        "profit_daily": "📊 Чистая прибыль за сегодня: {profit} сум",
        "profit_weekly": "📊 Чистая прибыль за неделю: {profit} сум",
        "profit_monthly": "📊 Чистая прибыль за месяц: {profit} сум",
        "profit_yearly": "📊 Чистая прибыль за год: {profit} сум",
        "profit_not_linked": "⚠️ Для работы этой команды сначала привяжите группу к вашему аккаунту на сайте (отправьте логин и пароль).",
        "profit_fetch_error": "❌ Не удалось получить данные. Попробуйте ещё раз чуть позже.",
    },
    "en": {
        "choose_language": "Tilni tanlang / Choose language / Выберите язык:",
        "language_set": "✅ Language set to English.",
        "welcome_offer": (
            "Hello, {name}!\n\n"
            "To use the service, please complete the payment. "
            "Price: {price} UZS/month.\n\n"
            "Tap the button below 👇"
        ),
        "btn_pay": "💳 Pay now",
        "card_payment_instructions": (
            "💳 Please make the payment to the following card:\n\n"
            "Card number: <code>{card_number}</code>\n"
            "Card holder: <b>{card_holder}</b>\n"
            "Amount: <b>{price} UZS</b>\n\n"
            "1️⃣ Tap the card number to copy it\n"
            "2️⃣ Pay via an ATM or any mobile banking app\n"
            "3️⃣ Send the payment receipt (screenshot or photo) here 👇"
        ),
        "receipt_invalid": "❗ Please send the payment receipt as an image (screenshot).",
        "receipt_received": (
            "✅ Your receipt has been received and sent for admin review.\n"
            "We'll notify you here once it's confirmed, please wait a bit."
        ),
        "payment_rejected_user": (
            "❌ Unfortunately, your payment was not confirmed.\n\n"
            "Reason: {reason}\n\n"
            "Please double check the payment and resend the receipt, "
            "or contact the admin."
        ),
        "admin_new_payment_request": (
            "🆕 New payment receipt!\n\n"
            "👤 User: {full_name} (@{username})\n"
            "🆔 Telegram ID: <code>{telegram_id}</code>\n"
            "💰 Expected amount: {price} UZS\n\n"
            "Check the receipt and choose one of the actions below 👇"
        ),
        "admin_already_handled": "⚠️ This payment request has already been reviewed.",
        "admin_ask_reject_reason": (
            "❗ Write the rejection reason — this text will be sent "
            "directly to the user.\n\n"
            'For example: "Receipt is unclear, please resend" or "Amount doesn\'t match".'
        ),
        "admin_reject_reason_saved": "✅ Reason saved and sent to the user.",
        "admin_approved_caption_suffix": "\n\n✅ <b>Approved</b> — {admin_name}",
        "admin_rejected_caption_suffix": "\n\n❌ <b>Rejected</b> — {admin_name}\nReason: {reason}",
        "admin_pending_reason_caption_suffix": "\n\n⏳ {admin_name} is writing the rejection reason...",
        "processing_payment": "⏳ Checking payment, please wait...",
        "payment_success": (
            "✅ Payment received successfully!\n\n"
            "🌐 Website: {website}\n\n"
            "🔑 Your personal login details:\n"
            "Login: <code>{login}</code>\n"
            "Password: <code>{password}</code>\n\n"
            "⚠️ Don't share these with anyone and save them — they won't be shown again."
        ),
        "payment_success_renewed": (
            "✅ Payment received successfully!\n\n"
            "🔓 Your login and password are reactivated — you can log in to the website again.\n"
            "🌐 Website: {website}\n"
            "Login: <code>{login}</code>"
        ),
        "already_paid": (
            "You have already completed the payment.\n\n"
            "🌐 Website: {website}\n"
            "🔑 Login: <code>{login}</code>\n"
            "🔑 Password: <code>{password}</code>"
        ),
        "subscription_expired": (
            "⏰ Your payment period has expired.\n\n"
            "Your login and password will stop working temporarily.\n"
            "If you make the payment again, your login and password will start working again."
        ),
        "tutorial_caption": (
            "🎬 A short video on how to use the bot 👆\n\n"
            "✅ A complete guide to using the bot is shown in this video\n"
            "📌 If you have questions, you can watch the video again anytime"
        ),
        "profit_daily": "📊 Today's net profit: {profit} UZS",
        "profit_weekly": "📊 This week's net profit: {profit} UZS",
        "profit_monthly": "📊 This month's net profit: {profit} UZS",
        "profit_yearly": "📊 This year's net profit: {profit} UZS",
        "profit_not_linked": "⚠️ To use this command, first link a group to your website account (send login and password there).",
        "profit_fetch_error": "❌ Couldn't fetch the data. Please try again shortly.",
    },
}


def t(language: str, key: str, **kwargs) -> str:
    text = TEXTS.get(language, TEXTS["uz"]).get(key, key)
    return text.format(**kwargs) if kwargs else text
