from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonCommands

COMMANDS_UZ = [
    BotCommand(command="start", description="Botni ishga tushirish / qayta boshlash"),
    BotCommand(command="menu", description="Hisobotlar menyusi"),
]


async def setup_bot_commands(bot: Bot) -> None:
    """Telegramning o'z Menu (ko'k) tugmasini sozlaydi — har qanday qurilmada ishlaydi."""
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
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
