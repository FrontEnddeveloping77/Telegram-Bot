from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

COMMANDS_UZ = [
    BotCommand(command="start", description="Botni ishga tushirish / qayta boshlash"),
    BotCommand(command="menu", description="Hisobotlar menyusi"),
    BotCommand(command="kunlik", description="Kunlik sof foyda"),
    BotCommand(command="haftalik", description="Haftalik sof foyda"),
    BotCommand(command="oylik", description="Oylik sof foyda"),
    BotCommand(command="yillik", description="Yillik sof foyda"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    for lang in ("uz", "ru", "en"):
        await bot.delete_my_commands(
            scope=BotCommandScopeDefault(),
            language_code=lang,
        )
    await bot.set_my_commands(
        commands=COMMANDS_UZ,
        scope=BotCommandScopeDefault(),
    )
