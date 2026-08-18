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
    "kunlik": "daily",
    "haftalik": "weekly",
    "oylik": "monthly",
    "yillik": "yearly",
}

PERIOD_TITLES = {
    "daily": "BUGUNGI HISOBOT",
    "weekly": "HAFTALIK HISOBOT",
    "monthly": "OYLIK HISOBOT",
    "yearly": "YILLIK HISOBOT",
}


async def _resolve_login(message: Message) -> tuple[str | None, str]:
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


def _fmt(value) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


async def _fetch_full_report(site_login: str, period: str) -> dict | None:
    """
    To'liq hisobot:
    { revenue, profit, expense, net_profit, sold, total_products, total_stock }
    """
    base = _api_base()

    # Yangi batafsil endpoint
    url = f"{base}/api/bot/report"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login, "period": period},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if isinstance(data, dict) and "net_profit" in data:
                        return data
                else:
                    logger.warning("report API status=%s", resp.status)
    except Exception:
        logger.exception("report API xato")

    # Fallback: eski profits endpoint (faqat sof foyda)
    url2 = f"{base}/api/bot/profits/{site_login}"
    field_map = {
        "daily": "dailyProfit",
        "weekly": "weeklyProfit",
        "monthly": "monthlyProfit",
        "yearly": "yearlyProfit",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url2, timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    field = field_map.get(period, "dailyProfit")
                    if isinstance(data, dict) and field in data:
                        net = float(data[field])
                        return {
                            "revenue": 0,
                            "profit": net,
                            "expense": 0,
                            "net_profit": net,
                            "sold": 0,
                            "total_products": 0,
                            "total_stock": 0,
                        }
    except Exception:
        logger.exception("profits fallback xato")

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
                    return None
                return await resp.json(content_type=None)
    except Exception:
        logger.exception("products xato")
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
                    return None
                return await resp.json(content_type=None)
    except Exception:
        logger.exception("top_category xato")
        return None


async def _fetch_warehouse(site_login: str) -> dict | None:
    url = f"{_api_base()}/api/bot/warehouse"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
    except Exception:
        logger.exception("warehouse xato")

    # Fallback: products dan hisoblash
    data = await _fetch_products(site_login)
    if data and "products" in data:
        products = data["products"] or []
        total_stock = sum(int(p.get("quantity") or 0) for p in products)
        return {
            "total_products": len(products),
            "total_stock": total_stock,
        }
    return None


def _format_full_report(period: str, data: dict) -> str:
    title = PERIOD_TITLES.get(period, "HISOBOT")
    revenue = data.get("revenue", 0)
    profit = data.get("profit", 0)
    expense = data.get("expense", 0)
    net = data.get("net_profit", 0)
    sold = data.get("sold", 0)
    total_products = data.get("total_products", 0)
    total_stock = data.get("total_stock", 0)

    net_icon = "🟢" if float(net) >= 0 else "🔴"
    net_label = "umumiy sof foyda"
    net_suffix = "" if float(net) >= 0 else " (ziyon)"

    # Period labels
    labels = {
        "daily": ("Bugungi", "Bugungi"),
        "weekly": ("Haftalik", "Haftalik"),
        "monthly": ("Oylik", "Oylik"),
        "yearly": ("Yillik", "Yillik"),
    }
    prefix, _ = labels.get(period, ("", ""))

    lines = [
        f"📊 <b>{title}</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🛒 <b>Sotilgan:</b> {_fmt(sold)} dona",
        f"💰 <b>{prefix} tushum:</b> {_fmt(revenue)} so'm",
        f"📈 <b>{prefix} foyda:</b> {_fmt(profit)} so'm",
        f"💸 <b>{prefix} rasxod:</b> {_fmt(expense)} so'm",
        f"{net_icon} <b>{prefix} {net_label}:</b> {_fmt(abs(float(net)))} so'm{net_suffix}",
        "━━━━━━━━━━━━━━━━━━━━",
        "📦 <b>OMBOR HOLATI</b>",
        f"🗂 <b>Jami tovar turi:</b> {_fmt(total_products)} xil",
        f"📊 <b>Jami qoldiq:</b> {_fmt(total_stock)} dona",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


async def _send_period_report(message: Message, period: str):
    site_login, language = await _resolve_login(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_full_report(site_login, period)
    if data is None:
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
        return

    await message.answer(
        _format_full_report(period, data),
        reply_markup=reports_keyboard(),
    )


@router.message(Command(commands=list(PERIOD_MAP.keys())))
async def cmd_profit_report(message: Message):
    command = message.text.split()[0].lstrip("/").split("@")[0]
    period = PERIOD_MAP[command]
    await _send_period_report(message, period)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    site_login, language = await _resolve_login(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return
    await message.answer(
        "📋 Hisobotlar menyusi. Kerakli tugmani bosing 👇",
        reply_markup=reports_keyboard(),
    )


@router.message(F.text == "📊 Oylik hisobot")
async def on_monthly(message: Message):
    await _send_period_report(message, "monthly")


@router.message(F.text == "📈 Yillik hisobot")
async def on_yearly(message: Message):
    await _send_period_report(message, "yearly")


@router.message(F.text.in_({"📅 Kunlik hisobot", "btn_daily_report"}))
async def on_daily(message: Message):
    await _send_period_report(message, "daily")


@router.message(F.text.in_({"📆 Haftalik hisobot", "btn_weekly_report"}))
async def on_weekly(message: Message):
    await _send_period_report(message, "weekly")


@router.message(F.text == "📦 Do'kondagi tovarlar")
async def on_store_products(message: Message):
    site_login, language = await _resolve_login(message)
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
            "📭 Do'konda hozircha tovarlar topilmadi.",
            reply_markup=reports_keyboard(),
        )
        return

    lines = ["📦 <b>Do'kondagi tovarlar:</b>", ""]
    for i, item in enumerate(products, 1):
        name = item.get("name") or "—"
        ptype = item.get("type") or item.get("category") or "—"
        qty = item.get("quantity") or 0
        total = item.get("total") or 0
        lines.append(
            f"{i}. <b>{name}</b>\n"
            f"   Turi: {ptype}\n"
            f"   Donasi: {_fmt(qty)}\n"
            f"   Jami: {_fmt(total)} so'm"
        )

    if total_sum is not None:
        lines.append("")
        lines.append(f"💰 <b>Umumiy summa: {_fmt(total_sum)} so'm</b>")

    await message.answer("\n".join(lines), reply_markup=reports_keyboard())


@router.message(F.text == "🏆 Top kategoriya")
async def on_top_category(message: Message):
    site_login, language = await _resolve_login(message)
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

    category = data.get("category") or "—"
    sold_count = data.get("sold_count") or 0
    total_amount = data.get("total_amount") or 0

    text = (
        f"🏆 <b>Eng ko'p sotilgan tovar kategoriyasi:</b> {category}\n"
        f"📦 <b>Sotilgan miqdor:</b> {_fmt(sold_count)}\n"
        f"💰 <b>Jami summa:</b> {_fmt(total_amount)} so'm"
    )
    await message.answer(text, reply_markup=reports_keyboard())


@router.message(F.text == "🏪 Ombor holati")
async def on_warehouse(message: Message):
    site_login, language = await _resolve_login(message)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_warehouse(site_login)
    if data is None:
        await message.answer(
            t(language, "profit_fetch_error"),
            reply_markup=reports_keyboard(),
        )
        return

    total_products = data.get("total_products", 0)
    total_stock = data.get("total_stock", 0)

    text = (
        "📦 <b>OMBOR HOLATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂 <b>Jami tovar turi:</b> {_fmt(total_products)} xil\n"
        f"📊 <b>Jami qoldiq:</b> {_fmt(total_stock)} dona\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=reports_keyboard())
