from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

COMMANDS = {
    "uz": [
        BotCommand(
            command="start", description="Botni ishga tushirish / qayta boshlash"
        ),
        BotCommand(command="language", description="Tilni almashtirish"),
        BotCommand(command="menu", description="Hisobotlar menyusi"),
        BotCommand(command="kunlik", description="Kunlik sof foyda"),
        BotCommand(command="haftalik", description="Haftalik sof foyda"),
        BotCommand(command="oylik", description="Oylik sof foyda"),
        BotCommand(command="yillik", description="Yillik sof foyda"),
    ],
    "ru": [
        BotCommand(command="start", description="Запустить / перезапустить бота"),
        BotCommand(command="language", description="Сменить язык"),
        BotCommand(command="menu", description="Меню отчётов"),
        BotCommand(command="kunlik", description="Чистая прибыль за день"),
        BotCommand(command="haftalik", description="Чистая прибыль за неделю"),
        BotCommand(command="oylik", description="Чистая прибыль за месяц"),
        BotCommand(command="yillik", description="Чистая прибыль за год"),
    ],
    "en": [
        BotCommand(command="start", description="Start / restart the bot"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="menu", description="Reports menu"),
        BotCommand(command="kunlik", description="Daily net profit"),
        BotCommand(command="haftalik", description="Weekly net profit"),
        BotCommand(command="oylik", description="Monthly net profit"),
        BotCommand(command="yillik", description="Yearly net profit"),
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
