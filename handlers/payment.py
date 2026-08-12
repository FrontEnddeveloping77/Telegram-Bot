from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import config
from database.requests import get_user, renew_or_activate_subscription
from locales.texts import t
from utils.keyboards import payment_methods_keyboard
from utils.credentials import (
    generate_unique_login,
    generate_strong_password,
    encrypt_password,
    decrypt_password,
    hash_password_for_site,
)
from payments.processor import process_payment

router = Router(name="payment")


@router.callback_query(F.data == "pay:start")
async def on_pay_start(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    language = user.language if user else "uz"

    if user and user.is_paid:
        password = decrypt_password(user.site_password_encrypted)
        await callback.message.answer(
            t(
                language,
                "already_paid",
                website=config.website_url,
                login=user.site_login,
                password=password,
            )
        )
        await callback.answer()
        return

    await callback.message.answer(
        t(language, "choose_payment_method"),
        reply_markup=payment_methods_keyboard(language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:method:"))
async def on_method_chosen(callback: CallbackQuery):
    method = callback.data.split(":", 2)[2]  # click | payme | other
    user = await get_user(callback.from_user.id)
    language = user.language if user else "uz"

    if method == "other":
        await callback.answer(t(language, "other_method_soon"), show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(t(language, "processing_payment"))

    success, payment_id = await process_payment(callback.from_user.id, method)

    if not success:
        # Kelajakda muvaffaqiyatsiz to'lov uchun alohida xabar qo'shish mumkin
        return

    # Bular faqat user BIRINCHI marta to'lov qilganda ishlatiladi.
    # Agar user avval login/parolga ega bo'lsa, quyidagilar e'tiborga olinmaydi —
    # bazadagi eski login va eski (shifrlangan) parol qaytariladi.
    candidate_login = await generate_unique_login()
    candidate_password = generate_strong_password()
    candidate_password_encrypted = encrypt_password(candidate_password)
    candidate_password_hash = hash_password_for_site(candidate_password)

    login, password_encrypted = await renew_or_activate_subscription(
        telegram_id=callback.from_user.id,
        payment_method=method,
        payment_id=payment_id,
        new_login=candidate_login,
        new_password_encrypted=candidate_password_encrypted,
        new_password_hash=candidate_password_hash,
    )

    # Har doim asl (bir marta yaratilgan, o'zgarmas) parolni ko'rsatamiz
    password = decrypt_password(password_encrypted)

    await callback.message.answer(
        t(
            language,
            "payment_success",
            website=config.website_url,
            login=login,
            password=password,
        )
    )
