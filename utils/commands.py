from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

COMMANDS = {
    "uz": [
        BotCommand(
            command="start", description="Botni ishga tushirish / qayta boshlash"
        ),
        BotCommand(command="language", description="Tilni almashtirish"),
    ],
    "ru": [
        BotCommand(command="start", description="Запустить / перезапустить бота"),
        BotCommand(command="language", description="Сменить язык"),
    ],
    "en": [
        BotCommand(command="start", description="Start / restart the bot"),
        BotCommand(command="language", description="Change language"),
    ],
}


async def setup_bot_commands(bot: Bot) -> None:
    """
    Har bir til uchun (uz/ru/en) alohida buyruq tavsiflarini o'rnatadi.
    Telegram, foydalanuvchining ilova tiliga qarab mos tavsifni ko'rsatadi.
    Standart (aniqlanmagan til uchun) inglizcha tavsif ishlatiladi.
    """
    await bot.set_my_commands(commands=COMMANDS["en"], scope=BotCommandScopeDefault())

    for language_code, commands in COMMANDS.items():
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeDefault(),
            language_code=language_code,
        )
