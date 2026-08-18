import logging

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from config import config
from database.requests import get_user, get_user_by_group_chat_id
from locales.texts import t
from utils.keyboards import reports_keyboard

router = Router(name="reports")
logger = logging.getLogger(__name__)

# buyruq -> (backendga yuboriladigan davr kodi, javob matni kaliti)
PERIOD_MAP = {
    "kunlik": ("daily", "profit_daily"),
    "haftalik": ("weekly", "profit_weekly"),
    "oylik": ("monthly", "profit_monthly"),
    "yillik": ("yearly", "profit_yearly"),
}


async def _resolve_login_and_language(message: Message) -> tuple[str | None, str]:
    """Buyruq qaysi login uchun ishlashini aniqlaydi: guruhda - bog'langan login, shaxsiy chatda - o'zining logini."""
    if message.chat.type == ChatType.PRIVATE:
        user = await get_user(message.from_user.id)
        if user and user.site_login and user.is_paid:
            return user.site_login, user.language
        return None, (user.language if user else "uz")

    user = await get_user_by_group_chat_id(message.chat.id)
    if user and user.site_login:
        return user.site_login, user.language
    return None, "uz"


async def _fetch_profit(site_login: str, period: str) -> float | None:
    url = f"{config.website_url.rstrip('/')}/api/bot/users_login"
    params = {"login": site_login, "period": period}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.warning("Profit API xato javob qaytardi: %s", resp.status)
                    return None
                data = await resp.json()
                return data.get("profit")
    except Exception:
        logger.exception("Profit so'rovida xatolik")
        return None


async def _fetch_products(site_login: str) -> dict | None:
    """
    Do'kondagi tovarlar ro'yxatini oladi.
    Kutilayotgan javob misoli:
    {
      "products": [
        {"name": "Olma", "type": "Meva", "quantity": 50, "total": 250000},
        ...
      ],
      "total_sum": 1500000
    }
    """
    url = f"{config.website_url.rstrip('/')}/api/bot/products"
    params = {"login": site_login}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    logger.warning("Products API xato javob qaytardi: %s", resp.status)
                    return None
                return await resp.json()
    except Exception:
        logger.exception("Products so'rovida xatolik")
        return None


async def _fetch_top_category(site_login: str) -> dict | None:
    """
    Eng ko'p sotilgan tovar kategoriyasini oladi.
    Kutilayotgan javob misoli:
    {
      "category": "Elektronika",
      "sold_count": 120,
      "total_amount": 4500000
    }
    """
    url = f"{config.website_url.rstrip('/')}/api/bot/top_category"
    params = {"login": site_login}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Top category API xato javob qaytardi: %s", resp.status
                    )
                    return None
                return await resp.json()
    except Exception:
        logger.exception("Top category so'rovida xatolik")
        return None


def _format_number(value) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


@router.message(Command(commands=list(PERIOD_MAP.keys())))
async def cmd_profit_report(message: Message):
    command = message.text.split()[0].lstrip("/").split("@")[0]
    period, text_key = PERIOD_MAP[command]

    site_login, language = await _resolve_login_and_language(message)

    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    profit = await _fetch_profit(site_login, period)

    if profit is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    formatted_profit = _format_number(profit)
    await message.answer(
        t(language, text_key, profit=formatted_profit),
        reply_markup=reports_keyboard(language),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Hisobotlar menyusini (kategoriya tugmalarini) ko'rsatadi."""
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return
    await message.answer(
        t(language, "reports_menu"),
        reply_markup=reports_keyboard(language),
    )


async def _handle_period_button(message: Message, period: str, text_key: str):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    profit = await _fetch_profit(site_login, period)
    if profit is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    formatted_profit = _format_number(profit)
    await message.answer(
        t(language, text_key, profit=formatted_profit),
        reply_markup=reports_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "📊 Oylik hisobot",
            "📊 Месячный отчёт",
            "📊 Monthly report",
        }
    )
)
async def on_monthly_report(message: Message):
    await _handle_period_button(message, "monthly", "profit_monthly")


@router.message(
    F.text.in_(
        {
            "📈 Yillik hisobot",
            "📈 Годовой отчёт",
            "📈 Yearly report",
        }
    )
)
async def on_yearly_report(message: Message):
    await _handle_period_button(message, "yearly", "profit_yearly")


@router.message(
    F.text.in_(
        {
            "📦 Do'kondagi tovarlar",
            "📦 Товары в магазине",
            "📦 Store products",
        }
    )
)
async def on_store_products(message: Message):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_products(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    products = data.get("products") or []
    total_sum = data.get("total_sum")

    if not products:
        await message.answer(
            t(language, "store_products_empty"),
            reply_markup=reports_keyboard(language),
        )
        return

    lines = [t(language, "store_products_header")]
    for i, item in enumerate(products, 1):
        name = item.get("name") or item.get("title") or "—"
        ptype = item.get("type") or item.get("category") or "—"
        qty = item.get("quantity") or item.get("qty") or 0
        total = item.get("total") or item.get("sum") or 0
        lines.append(
            t(
                language,
                "store_products_item",
                index=i,
                name=name,
                type=ptype,
                quantity=_format_number(qty),
                total=_format_number(total),
            )
        )

    if total_sum is not None:
        lines.append("")
        lines.append(
            t(language, "store_products_total", total=_format_number(total_sum))
        )

    await message.answer(
        "\n".join(lines),
        reply_markup=reports_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "🏆 Top kategoriya",
            "🏆 Топ категория",
            "🏆 Top category",
        }
    )
)
async def on_top_category(message: Message):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_top_category(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    category = data.get("category") or data.get("name") or "—"
    sold_count = data.get("sold_count") or data.get("quantity") or data.get("count")
    total_amount = data.get("total_amount") or data.get("total") or data.get("sum")

    text = t(language, "top_category_result", category=category)
    if sold_count is not None:
        text += "\n" + t(
            language, "top_category_sold", count=_format_number(sold_count)
        )
    if total_amount is not None:
        text += "\n" + t(
            language, "top_category_amount", amount=_format_number(total_amount)
        )

    await message.answer(text, reply_markup=reports_keyboard(language))
