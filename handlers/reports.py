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

PERIOD_MAP = {
    "kunlik": ("daily", "profit_daily"),
    "haftalik": ("weekly", "profit_weekly"),
    "oylik": ("monthly", "profit_monthly"),
    "yillik": ("yearly", "profit_yearly"),
}

PERIOD_TO_FIELD = {
    "daily": "dailyProfit",
    "weekly": "weeklyProfit",
    "monthly": "monthlyProfit",
    "yearly": "yearlyProfit",
}


async def _resolve_login_and_language(message: Message) -> tuple[str | None, str]:
    if message.chat.type == ChatType.PRIVATE:
        user = await get_user(message.from_user.id)
        if user and user.site_login and user.is_paid:
            return user.site_login, "uz"
        return None, "uz"

    user = await get_user_by_group_chat_id(message.chat.id)
    if user and user.site_login:
        return user.site_login, "uz"
    return None, "uz"


def _api_base() -> str:
    base = (getattr(config, "api_url", None) or "").strip()
    if not base:
        base = (config.website_url or "").strip()
    if not base or "frontend" in base:
        base = "https://sotuv-menejer-backend.vercel.app"
    return base.rstrip("/")


async def _fetch_profit(site_login: str, period: str) -> float | None:
    base = _api_base()
    field = PERIOD_TO_FIELD.get(period, "dailyProfit")

    url1 = f"{base}/api/bot/profits/{site_login}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url1, timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                raw = await resp.text()
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        data = None
                    if isinstance(data, dict) and field in data:
                        return float(data[field])
                    logger.warning(
                        "profits API maydon yo'q: field=%s data=%s", field, data
                    )
                else:
                    logger.warning(
                        "profits API status=%s body=%s", resp.status, raw[:200]
                    )
    except Exception:
        logger.exception("profits API xato: %s", url1)

    url2 = f"{base}/api/bot/users_login"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url2,
                params={"login": site_login, "period": period},
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                if resp.status != 200:
                    logger.warning("users_login API status=%s", resp.status)
                    return None
                data = await resp.json(content_type=None)
                if isinstance(data, dict) and "profit" in data:
                    return float(data["profit"])
    except Exception:
        logger.exception("users_login API xato: %s", url2)

    return None


async def _fetch_products(site_login: str) -> dict | None:
    url = f"{_api_base()}/api/bot/products"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Products API status=%s", resp.status)
                    return None
                return await resp.json(content_type=None)
    except Exception:
        logger.exception("Products so'rovida xatolik")
        return None


async def _fetch_top_category(site_login: str) -> dict | None:
    url = f"{_api_base()}/api/bot/top_category"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Top category API status=%s", resp.status)
                    return None
                return await resp.json(content_type=None)
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
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
        return

    await message.answer(
        t(language, text_key, profit=_format_number(profit)),
        reply_markup=reports_keyboard(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return
    await message.answer(
        t(language, "reports_menu"),
        reply_markup=reports_keyboard(),
    )


async def _handle_period_button(message: Message, period: str, text_key: str):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    profit = await _fetch_profit(site_login, period)
    if profit is None:
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
        return

    await message.answer(
        t(language, text_key, profit=_format_number(profit)),
        reply_markup=reports_keyboard(),
    )


@router.message(F.text == "📊 Oylik hisobot")
async def on_monthly_report(message: Message):
    await _handle_period_button(message, "monthly", "profit_monthly")


@router.message(F.text == "📈 Yillik hisobot")
async def on_yearly_report(message: Message):
    await _handle_period_button(message, "yearly", "profit_yearly")


@router.message(F.text.in_({"📅 Kunlik hisobot", "btn_daily_report"}))
async def on_daily_report(message: Message):
    await _handle_period_button(message, "daily", "profit_daily")


@router.message(F.text.in_({"📆 Haftalik hisobot", "btn_weekly_report"}))
async def on_weekly_report(message: Message):
    await _handle_period_button(message, "weekly", "profit_weekly")


@router.message(F.text == "📦 Do'kondagi tovarlar")
async def on_store_products(message: Message):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_products(site_login)
    if data is None:
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
        return

    products = data.get("products") or []
    total_sum = data.get("total_sum")

    if not products:
        await message.answer(
            t(language, "store_products_empty"),
            reply_markup=reports_keyboard(),
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
        reply_markup=reports_keyboard(),
    )


@router.message(F.text == "🏆 Top kategoriya")
async def on_top_category(message: Message):
    site_login, language = await _resolve_login_and_language(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_top_category(site_login)
    if data is None:
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
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

    await message.answer(text, reply_markup=reports_keyboard())
