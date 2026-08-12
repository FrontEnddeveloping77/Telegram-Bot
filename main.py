import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database.engine import init_db
from handlers import start, payment, group, reports
from utils.scheduler import subscription_expiry_watcher
from utils.notifications_watcher import notifications_watcher
from utils.commands import setup_bot_commands

logging.basicConfig(level=logging.INFO)


async def main():
    if not config.bot_token:
        raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan")

    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(group.router)
    dp.include_router(reports.router)

    await setup_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    # Obuna tugashini kuzatib turadigan fon vazifasini ishga tushirish
    asyncio.create_task(subscription_expiry_watcher(bot))
    # Sayt tomonidan yozilgan bildirishnomalarni guruhga yuboradigan fon vazifasini ishga tushirish
    asyncio.create_task(notifications_watcher(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
