import logging
import asyncio
from typing import Optional, Tuple

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType

from config import config
from database.requests import get_user, get_user_by_group_chat_id
from locales.texts import t
from utils.keyboards import reports_keyboard, clear_old_reply_keyboard

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


async def _resolve_login(
    message: Message, user_id: Optional[int] = None
) -> Tuple[Optional[str], str]:
    uid = user_id if user_id is not None else message.from_user.id
    if message.chat.type == ChatType.PRIVATE:
        user = await get_user(uid)
        if user and user.site_login and user.is_paid:
            return user.site_login, "uz"
        return None, "uz"

    user = await get_user_by_group_chat_id(message.chat.id)
    if user and user.site_login:
        return user.site_login, "uz"
    return None, "uz"


def _api_base() -> str:
    """
    Backend API manzili.
    Eski Vercel backend o'chirilgan, shuning uchun fallback ham yangilandi.
    """
    base = (getattr(config, "api_url", None) or "").strip()
    if not base:
        base = (getattr(config, "website_url", None) or "").strip()
    # Frontend domeni, eski Vercel yoki bo'sh bo'lsa — to'g'ri API ga o'tamiz
    if (
        not base
        or "frontend" in base
        or base.rstrip("/") in ("https://sotuvmenejer.uz", "http://sotuvmenejer.uz")
        or "vercel.app" in base
    ):
        base = "https://api.sotuvmenejer.uz"
    return base.rstrip("/")


def _fmt(value) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


# ====================== FETCH FUNKSIYALARI ======================


async def _fetch_products(site_login: str):
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


async def _fetch_warehouse(site_login: str):
    """Ombor ma'lumotini oladi + total_sum ni kafolatlaydi"""
    url = f"{_api_base()}/api/bot/warehouse"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if isinstance(data, dict):
                        # total_sum yo'q bo'lsa products dan olamiz
                        if data.get("total_sum") is None:
                            products_data = await _fetch_products(site_login)
                            if products_data:
                                if products_data.get("total_sum") is not None:
                                    data["total_sum"] = products_data["total_sum"]
                                elif "products" in products_data:
                                    data["total_sum"] = sum(
                                        float(p.get("total") or 0)
                                        for p in (products_data["products"] or [])
                                    )
                        return data
    except Exception:
        logger.exception("warehouse xato")

    # Fallback
    data = await _fetch_products(site_login)
    if data and "products" in data:
        products = data["products"] or []
        total_stock = sum(int(p.get("quantity") or 0) for p in products)
        total_sum = data.get("total_sum")
        if total_sum is None:
            total_sum = sum(float(p.get("total") or 0) for p in products)
        return {
            "total_products": len(products),
            "total_stock": total_stock,
            "total_sum": total_sum,
        }
    return None


async def _fetch_full_report(site_login: str, period: str):
    """Asosiy hisobot + omborni majburiy qo'shadi"""
    base = _api_base()
    url = f"{base}/api/bot/report"

    # 1-urinish: asosiy report
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login, "period": period},
                timeout=aiohttp.ClientTimeout(total=18),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if isinstance(data, dict) and (
                        "net_profit" in data or "profit" in data
                    ):
                        # Ombor ma'lumotini alohida olish
                        warehouse = await _fetch_warehouse(site_login)
                        if warehouse:
                            data["total_products"] = warehouse.get(
                                "total_products", data.get("total_products", 0)
                            )
                            data["total_stock"] = warehouse.get(
                                "total_stock", data.get("total_stock", 0)
                            )
                            data["total_sum"] = warehouse.get(
                                "total_sum", data.get("total_sum")
                            )
                        return data
                else:
                    logger.warning(
                        "report API status=%s | login=%s | period=%s",
                        resp.status,
                        site_login,
                        period,
                    )
    except Exception as e:
        logger.exception("report API xato: %s", e)

    # 2-urinish: profits fallback + ombor
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
                        net = float(data[field] or 0)

                        warehouse = await _fetch_warehouse(site_login)
                        total_products = (
                            warehouse.get("total_products", 0) if warehouse else 0
                        )
                        total_stock = (
                            warehouse.get("total_stock", 0) if warehouse else 0
                        )
                        total_sum = warehouse.get("total_sum") if warehouse else None

                        return {
                            "revenue": float(data.get("revenue") or 0),
                            "profit": float(data.get("profit") or net),
                            "expense": float(data.get("expense") or 0),
                            "net_profit": net,
                            "sold": int(data.get("sold") or 0),
                            "total_products": total_products,
                            "total_stock": total_stock,
                            "total_sum": total_sum,
                        }
    except Exception as e:
        logger.exception("profits fallback xato: %s", e)

    return None


async def _fetch_top_category(site_login: str):
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


async def _fetch_debts(site_login: str):
    url = f"{_api_base()}/api/bot/debts"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("debts API status=%s", resp.status)
                    return None
                return await resp.json(content_type=None)
    except Exception:
        logger.exception("debts xato")
        return None


async def _fetch_customer_debts(site_login: str):
    url = f"{_api_base()}/api/bot/customer-debts"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"login": site_login},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("customer-debts API status=%s", resp.status)
                    return None
                return await resp.json(content_type=None)
    except Exception:
        logger.exception("customer-debts xato")
        return None


# ====================== FORMAT FUNKSIYALARI ======================


def _format_full_report(period: str, data: dict) -> str:
    title = PERIOD_TITLES.get(period, "HISOBOT")
    revenue = data.get("revenue", 0)
    profit = data.get("profit", 0)
    expense = data.get("expense", 0)
    net = data.get("net_profit", 0)
    sold = data.get("sold", 0)
    total_products = data.get("total_products", 0)
    total_stock = data.get("total_stock", 0)
    total_sum = data.get("total_sum")

    net_icon = "🟢" if float(net) >= 0 else "🔴"
    net_label = "umumiy sof foyda"
    net_suffix = "" if float(net) >= 0 else " (ziyon)"

    labels = {
        "daily": "Bugungi",
        "weekly": "Haftalik",
        "monthly": "Oylik",
        "yearly": "Yillik",
    }
    prefix = labels.get(period, "")

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
    ]

    if total_sum is not None:
        lines.append(f"💰 <b>Jami summa:</b> {_fmt(total_sum)} so'm")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ====================== HANDLER FUNKSIYALARI ======================


async def _send_period_report(
    message: Message, period: str, user_id: Optional[int] = None
):
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_full_report(site_login, period)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    await message.answer(_format_full_report(period, data))


async def _do_full_report(message: Message, user_id: Optional[int] = None):
    """To'liq hisobot — barcha muhim ma'lumotlar bir joyda"""
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    daily_task = _fetch_full_report(site_login, "daily")
    warehouse_task = _fetch_warehouse(site_login)
    debts_task = _fetch_debts(site_login)
    customer_debts_task = _fetch_customer_debts(site_login)
    top_task = _fetch_top_category(site_login)

    daily, warehouse, debts, customer_debts, top = await asyncio.gather(
        daily_task,
        warehouse_task,
        debts_task,
        customer_debts_task,
        top_task,
        return_exceptions=True,
    )

    lines = [
        "📊 <b>TO‘LIQ HISOBOT</b>",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    # Bugungi holat
    if isinstance(daily, dict):
        revenue = daily.get("revenue", 0)
        profit = daily.get("profit", 0)
        expense = daily.get("expense", 0)
        net = daily.get("net_profit", 0)
        sold = daily.get("sold", 0)
        net_icon = "🟢" if float(net) >= 0 else "🔴"

        lines.extend(
            [
                "📅 <b>BUGUNGI HOLAT</b>",
                f"🛒 Sotilgan: {_fmt(sold)} dona",
                f"💰 Tushum: {_fmt(revenue)} so'm",
                f"📈 Foyda: {_fmt(profit)} so'm",
                f"💸 Rasxod: {_fmt(expense)} so'm",
                f"{net_icon} Sof foyda: {_fmt(abs(float(net)))} so'm",
                "━━━━━━━━━━━━━━━━━━━━",
            ]
        )
    else:
        lines.append("⚠️ Bugungi ma'lumot olinmadi\n━━━━━━━━━━━━━━━━━━━━")

    # Ombor
    if isinstance(warehouse, dict):
        total_products = warehouse.get("total_products", 0)
        total_stock = warehouse.get("total_stock", 0)
        total_sum = warehouse.get("total_sum")

        lines.extend(
            [
                "📦 <b>OMBOR HOLATI</b>",
                f"🗂 Tovar turi: {_fmt(total_products)} xil",
                f"📊 Qoldiq: {_fmt(total_stock)} dona",
            ]
        )
        if total_sum is not None:
            lines.append(f"💰 Jami summa: {_fmt(total_sum)} so'm")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
    else:
        lines.append("⚠️ Ombor ma'lumoti olinmadi\n━━━━━━━━━━━━━━━━━━━━")

    # Top kategoriya
    if isinstance(top, dict):
        category = top.get("category") or "—"
        sold_count = top.get("sold_count") or 0
        total_amount = top.get("total_amount") or 0
        lines.extend(
            [
                "🏆 <b>TOP KATEGORIYA</b>",
                f"🥇 {category}",
                f"📦 Sotilgan: {_fmt(sold_count)} · 💰 {_fmt(total_amount)} so'm",
                "━━━━━━━━━━━━━━━━━━━━",
            ]
        )

    # Qarzlar
    our_debt = 0
    if isinstance(debts, dict):
        our_debt = debts.get("total_debt") or 0

    customer_debt = 0
    if isinstance(customer_debts, dict):
        customer_debt = customer_debts.get("total_debt") or 0

    lines.extend(
        [
            "💸 <b>QARZLAR</b>",
            f"📉 Bizning qarzimiz: {_fmt(our_debt)} so'm",
            f"👥 Bizga qarzdorlar: {_fmt(customer_debt)} so'm",
            "━━━━━━━━━━━━━━━━━━━━",
        ]
    )

    await message.answer("\n".join(lines))


async def _do_store_products(message: Message, user_id: Optional[int] = None):
    site_login, language = await _resolve_login(message, user_id)
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
        await message.answer("📭 Do'konda hozircha tovarlar topilmadi.")
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

    await message.answer("\n".join(lines))


async def _do_top_category(message: Message, user_id: Optional[int] = None):
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_top_category(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    category = data.get("category") or "—"
    sold_count = data.get("sold_count") or 0
    total_amount = data.get("total_amount") or 0

    top_size = data.get("top_size") or "—"
    top_size_sold = data.get("top_size_sold") or 0
    top_size_amount = data.get("top_size_amount") or 0

    top_color = data.get("top_color") or "—"
    top_color_sold = data.get("top_color_sold") or 0
    top_color_amount = data.get("top_color_amount") or 0

    stock_size = data.get("stock_size") or "—"
    stock_size_qty = data.get("stock_size_qty") or 0

    stock_category = data.get("stock_category") or "—"
    stock_category_qty = data.get("stock_category_qty") or 0

    text = (
        "🏆 <b>TOP STATISTIKA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Eng ko'p sotilgan kategoriya:</b> {category}\n"
        f"📦 Sotilgan miqdor: {_fmt(sold_count)}\n"
        f"💰 Jami summa: {_fmt(total_amount)} so'm\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📏 <b>Eng ko'p sotilgan razmer:</b> {top_size}\n"
        f"📦 Sotilgan miqdor: {_fmt(top_size_sold)}\n"
        f"💰 Jami summa: {_fmt(top_size_amount)} so'm\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 <b>Eng ko'p sotilgan rang:</b> {top_color}\n"
        f"📦 Sotilgan miqdor: {_fmt(top_color_sold)}\n"
        f"💰 Jami summa: {_fmt(top_color_amount)} so'm\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 <b>Eng ko'p turib qolgan razmer:</b> {stock_size}\n"
        f"📊 Qoldiq: {_fmt(stock_size_qty)} dona\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂 <b>Eng ko'p turib qolgan kategoriya:</b> {stock_category}\n"
        f"📊 Qoldiq: {_fmt(stock_category_qty)} dona\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text)


async def _do_warehouse(message: Message, user_id: Optional[int] = None):
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_warehouse(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    total_products = data.get("total_products", 0)
    total_stock = data.get("total_stock", 0)
    total_sum = data.get("total_sum")

    text = (
        "📦 <b>OMBOR HOLATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂 <b>Jami tovar turi:</b> {_fmt(total_products)} xil\n"
        f"📊 <b>Jami qoldiq:</b> {_fmt(total_stock)} dona\n"
    )

    if total_sum is not None:
        text += f"💰 <b>Jami summa:</b> {_fmt(total_sum)} so'm\n"

    text += "━━━━━━━━━━━━━━━━━━━━"
    await message.answer(text)


async def _do_total_debt_ours(message: Message, user_id: Optional[int] = None):
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_debts(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    debts = data.get("debts") or []
    total_debt = data.get("total_debt") or 0

    if not debts:
        await message.answer(
            "💸 <b>JAMI QARZIMIZ</b>\n\n"
            "✅ Hozircha tovar berganlarga ochiq qarz yo‘q."
        )
        return

    lines = [
        "💸 <b>JAMI QARZIMIZ</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📉 <b>Jami qarz:</b> {_fmt(total_debt)} so'm",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, d in enumerate(debts, 1):
        name = d.get("supplier") or "—"
        phone = d.get("supplier_phone") or ""
        debt = d.get("debt") or 0
        paid = d.get("total_paid") or 0
        cost = d.get("total_cost") or 0
        cats = d.get("categories") or []
        cat_str = ", ".join(cats) if cats else "—"
        block = (
            f"{i}. <b>{name}</b>\n"
            + (f"   📞 {phone}\n" if phone else "")
            + f"   🗂 {cat_str}\n"
            + f"   💰 Jami: {_fmt(cost)}"
            + f"   💰 To‘langan: {_fmt(paid)}\n"
            + f"   📉 Qarz: <b>{_fmt(debt)} so'm</b>"
        )
        lines.append(block)
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    await message.answer("\n".join(lines))


async def _do_debtors(message: Message, user_id: Optional[int] = None):
    site_login, language = await _resolve_login(message, user_id)
    if not site_login:
        await message.answer(t(language, "profit_not_linked"))
        return

    data = await _fetch_customer_debts(site_login)
    if data is None:
        await message.answer(t(language, "profit_fetch_error"))
        return

    debts = data.get("debts") or []
    total_debt = data.get("total_debt") or 0

    if not debts:
        await message.answer(
            "👥 <b>BIZGA QARZDORLAR</b>\n\n" "✅ Hozircha mijozlardan ochiq qarz yo‘q."
        )
        return

    lines = [
        "👥 <b>BIZGA QARZDORLAR</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📉 <b>Jami mijoz qarzi:</b> {_fmt(total_debt)} so'm",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, d in enumerate(debts, 1):
        name = d.get("customer_name") or "—"
        phone = d.get("customer_phone") or ""
        debt = d.get("debt") or 0
        paid = d.get("total_paid") or 0
        total = d.get("total_amount") or 0
        cnt = d.get("sales_count") or 0
        block = (
            f"{i}. <b>{name}</b>\n"
            + (f"   📞 {phone}\n" if phone else "")
            + f"   🛒 Sotuvlar: {cnt} ta\n"
            + f"   💰 Jami: {_fmt(total)} · To‘langan: {_fmt(paid)}\n"
            + f"   📉 Qarz: <b>{_fmt(debt)} so'm</b>"
        )
        lines.append(block)
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    await message.answer("\n".join(lines))


# ====================== ROUTER HANDLERS ======================


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
    await clear_old_reply_keyboard(message)
    await message.answer(
        "📋 Hisobotlar menyusi. Kerakli tugmani bosing 👇\n"
        "Yoki chap tomondagi <b>Menu</b> tugmasidan buyruqlarni tanlang.",
        reply_markup=reports_keyboard(),
    )


@router.message(F.text == "📊 To‘liq hisobot")
@router.message(Command("tolik", "full", "hisobot"))
async def on_full_report(message: Message):
    await _do_full_report(message)


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
@router.message(Command("tovarlar"))
async def on_store_products(message: Message):
    await _do_store_products(message)


@router.message(F.text == "🏆 Top kategoriya")
@router.message(Command("top"))
async def on_top_category(message: Message):
    await _do_top_category(message)


@router.message(F.text == "🏪 Ombor holati")
@router.message(Command("ombor"))
async def on_warehouse(message: Message):
    await _do_warehouse(message)


@router.message(F.text == "💸 Jami qarzimiz")
@router.message(Command("jamiqarz"))
async def on_total_debt_ours(message: Message):
    await _do_total_debt_ours(message)


@router.message(F.text == "👥 Bizga qarzdorlar")
@router.message(Command("bizgaqarz"))
async def on_debtors(message: Message):
    await _do_debtors(message)


# ====================== INLINE CALLBACKS ======================

_CALLBACK_TO_PERIOD = {
    "rep:monthly": "monthly",
    "rep:yearly": "yearly",
    "rep:daily": "daily",
    "rep:weekly": "weekly",
}


@router.callback_query(F.data.in_(_CALLBACK_TO_PERIOD.keys()))
async def cb_period_report(callback: CallbackQuery):
    await callback.answer()
    period = _CALLBACK_TO_PERIOD[callback.data]
    await _send_period_report(callback.message, period, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:full")
async def cb_full_report(callback: CallbackQuery):
    await callback.answer()
    await _do_full_report(callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:products")
async def cb_store_products(callback: CallbackQuery):
    await callback.answer()
    await _do_store_products(callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:top")
async def cb_top_category(callback: CallbackQuery):
    await callback.answer()
    await _do_top_category(callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:warehouse")
async def cb_warehouse(callback: CallbackQuery):
    await callback.answer()
    await _do_warehouse(callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:debt_ours")
async def cb_total_debt_ours(callback: CallbackQuery):
    await callback.answer()
    await _do_total_debt_ours(callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data == "rep:debtors")
async def cb_debtors(callback: CallbackQuery):
    await callback.answer()
    await _do_debtors(callback.message, user_id=callback.from_user.id)