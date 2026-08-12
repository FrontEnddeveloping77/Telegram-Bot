import logging

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from config import config
from database.requests import get_user, get_user_by_group_chat_id
from locales.texts import t

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

    formatted_profit = f"{profit:,.0f}".replace(",", " ")
    await message.answer(t(language, text_key, profit=formatted_profit))
