"""
Tariflar moduli.

Foydalanuvchilar tovar soni (ID) va Telegram guruhlar soniga qarab
oylik to'lov tariflarini tanlaydilar:

1. 1 000 tagacha ID (tovar):
   - 1 ta guruh: 299 000 so'm
   - 2 ta guruh: 339 000 so'm (+40 000)
   - 3-5 ta guruh: 399 000 so'm (+100 000)
   - 5 tadan ko'p guruh: @ABDULAZIZ_AVAZOV ga murojaat

2. Har keyingi 1 000 ta ID tovar qo'shilganda:
   - Bazaviy narxga +130 000 so'm (3-5 guruhlik qo'shimchasi 100k dan +30k ko'p)
   - 2 ta guruh: Base + 40 000 so'm
   - 3-5 ta guruh: Base + 100 000 so'm

3. 5 000 tadan ko'p tovar yoki 5 tadan ko'p guruh:
   Admin bilan to'g'ridan-to'g'ri bog'lanish: @ABDULAZIZ_AVAZOV
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

ADMIN_USERNAME = "ABDULAZIZ_AVAZOV"
ADMIN_CONTACT_URL = f"https://t.me/{ADMIN_USERNAME}"

# Qo'llab-quvvatlanadigan tovar toifalari (ID lar soni)
AVAILABLE_PRODUCT_TIERS = [1000, 2000, 3000, 4000, 5000]

# Guruh variantlari: (max_groups, ko'rsatiladigan nom)
GROUP_OPTIONS = [
    (1, "1 ta guruh"),
    (2, "2 ta guruh"),
    (5, "3-5 ta guruh"),
]


def format_price(amount: int | None) -> str:
    """Narxni chiroyli ko'rinishda formatlash: 299000 -> '299 000'"""
    if amount is None:
        return "0"
    return f"{amount:,}".replace(",", " ")


def calculate_tariff_price(max_products: int, max_groups: int) -> int | None:
    """
    Berilgan tovar soni va guruhlar soni bo'yicha oylik to'lov summasini hisoblaydi.

    1 000 ta ID:
      1 guruh: 299 000 so'm
      2 guruh: 339 000 so'm (+40 000 so'm)
      3-5 guruh: 399 000 so'm (+100 000 so'm)

    Har keyingi 1 000 ta ID uchun oldingisiga +130 000 so'm qo'shiladi (100k + 30k).
    2 guruh har doim bazaviy + 40 000 so'm.
    3-5 guruh har doim bazaviy + 100 000 so'm.
    """
    if max_products < 1000 or max_products > 5000:
        return None

    tier_idx = (max_products // 1000) - 1
    base_price = 299_000 + (tier_idx * 130_000)

    if max_groups == 1:
        return base_price
    elif max_groups == 2:
        return base_price + 40_000
    elif 3 <= max_groups <= 5:
        return base_price + 100_000

    return None


def get_tariff_details(max_products: int, max_groups: int) -> dict:
    """Tarif haqida to'liq ma'lumot qaytaradi."""
    price = calculate_tariff_price(max_products, max_groups)
    group_label = "1 ta guruh" if max_groups == 1 else ("2 ta guruh" if max_groups == 2 else "3-5 ta guruh")
    return {
        "max_products": max_products,
        "max_groups": max_groups,
        "group_label": group_label,
        "price": price,
        "formatted_price": format_price(price),
    }


def calculate_upgrade_proration(
    old_monthly_price: int,
    new_monthly_price: int,
    expires_at,
) -> dict | None:
    """
    Tarifni oshirishda qolgan kunlar uchun to'lanadigan farqni hisoblaydi.
    Masalan:
    - Obuna tugashiga 5 kun qolgan
    - Eski tarif (1000 tovar): 299 000 / 30 * 5 = 49 833 so'm
    - Yangi tarif (2000 tovar): 499 000 / 30 * 5 = 83 167 so'm
    - Farqi: 83 167 - 49 833 = 33 334 so'm (yaxlitlangan: 33 000 so'm)
    """
    import math
    from datetime import datetime, timezone

    if new_monthly_price <= old_monthly_price:
        return None

    now = datetime.now(timezone.utc)
    if expires_at <= now:
        return None

    # Qolgan kunlar sonini aniqlash (kamida 1 kun)
    remaining_seconds = (expires_at - now).total_seconds()
    remaining_days = max(1, math.ceil(remaining_seconds / 86400))

    # Oylik asos: 30 kun
    old_daily = old_monthly_price / 30.0
    new_daily = new_monthly_price / 30.0

    old_remaining_cost = round(old_daily * remaining_days)
    new_remaining_cost = round(new_daily * remaining_days)

    diff = new_remaining_cost - old_remaining_cost
    # 1 000 so'mga yaxlitlash (yoki kamida 1 000)
    rounded_diff = max(1000, round(diff / 1000) * 1000)

    return {
        "remaining_days": remaining_days,
        "old_daily": round(old_daily),
        "new_daily": round(new_daily),
        "old_remaining_cost": old_remaining_cost,
        "new_remaining_cost": new_remaining_cost,
        "upgrade_amount": rounded_diff,
        "formatted_upgrade_amount": format_price(rounded_diff),
        "formatted_old_remaining": format_price(old_remaining_cost),
        "formatted_new_remaining": format_price(new_remaining_cost),
    }


# ===================== Klaviaturalar =====================


def products_selection_keyboard() -> InlineKeyboardMarkup:
    """Tovar soni (ID) oralig'ini tanlash klaviaturasi."""
    builder = InlineKeyboardBuilder()

    for tier in AVAILABLE_PRODUCT_TIERS:
        builder.button(
            text=f"📦 {format_price(tier)} tagacha tovar (ID)",
            callback_data=f"tariff:prod:{tier}",
        )

    # 5 000 tadan ko'p tovar yoki 5 tadan ko'p guruh uchun adminga murojaat
    builder.button(
        text="💬 5 000+ tovar yoki 5+ guruh (Maxsus tarif)",
        url=ADMIN_CONTACT_URL,
    )
    builder.adjust(1)
    return builder.as_markup()


def groups_selection_keyboard(max_products: int) -> InlineKeyboardMarkup:
    """Tanlangan tovar toifasi uchun guruh sonini tanlash klaviaturasi."""
    builder = InlineKeyboardBuilder()

    for groups, label in GROUP_OPTIONS:
        price = calculate_tariff_price(max_products, groups)
        builder.button(
            text=f"{label} — {format_price(price)} so'm/oy",
            callback_data=f"tariff:select:{max_products}:{groups}",
        )

    # 5 tadan ko'p guruh uchun adminga murojaat
    builder.button(
        text="💬 5 tadan ko'p guruh (@ABDULAZIZ_AVAZOV)",
        url=ADMIN_CONTACT_URL,
    )
    # Orqaga tugmasi
    builder.button(
        text="⬅️ Boshqa tovar sonini tanlash",
        callback_data="tariff:back_to_products",
    )
    builder.adjust(1)
    return builder.as_markup()


def tariff_confirmation_keyboard(max_products: int, max_groups: int) -> InlineKeyboardMarkup:
    """Tanlangan tarifni tasdiqlash va to'lovga o'tish klaviaturasi."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 To'lov qilish",
        callback_data="pay:start",
    )
    builder.button(
        text="🔄 Tarifni o'zgartirish",
        callback_data="tariff:back_to_products",
    )
    builder.button(
        text="💬 Savollar bo'yicha bog'lanish",
        url=ADMIN_CONTACT_URL,
    )
    builder.adjust(1)
    return builder.as_markup()


def upgrade_confirmation_keyboard(upgrade_amount: int) -> InlineKeyboardMarkup:
    """Tarifni oshirish uchun farqni to'lash klaviaturasi."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💳 Farqni to'lash ({format_price(upgrade_amount)} so'm)",
        callback_data="pay:start",
    )
    builder.button(
        text="🔄 Boshqa tarif tanlash",
        callback_data="tariff:back_to_products",
    )
    builder.button(
        text="⬅️ Bekor qilish",
        callback_data="tariff:cancel_upgrade",
    )
    builder.adjust(1)
    return builder.as_markup()
