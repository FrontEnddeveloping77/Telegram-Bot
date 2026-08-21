import re

import bcrypt
from aiogram import Router, F, Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import Message, ChatMemberUpdated

from database.requests import get_user_by_login, link_group_to_user

router = Router(name="group")

# Login va parolni bitta xabarda, bo'shliq bilan ajratilgan holda qabul qiladi: "user482913 aB3xY9Zk1Qw2"
_CREDENTIALS_PATTERN = re.compile(r"^(\S+)\s+(\S+)$")


@router.my_chat_member()
async def on_bot_added_to_group(event: ChatMemberUpdated):
    """Bot biror guruhga a'zo/admin qilib qo'shilganda ishga tushadi."""
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    just_added = old_status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    ) and new_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
    )

    if just_added:
        await event.bot.send_message(
            event.chat.id,
            "👋 Salom! Ushbu guruhni saytdagi hisobingizga bog'lash uchun, "
            "guruh admini quyidagi formatda login va parolni yuborsin:\n\n"
            "<code>login parol</code>\n\n"
            "Masalan: <code>user482913 aB3xY9Zk1Qw2</code>",
        )


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.regexp(_CREDENTIALS_PATTERN),
)
async def on_credentials_submitted(message: Message, bot: Bot):
    """Guruhda 'login parol' formatida yuborilgan xabarni tekshiradi va guruhni bog'laydi."""
    match = _CREDENTIALS_PATTERN.match(message.text)
    if not match:
        return

    login, password = match.group(1), match.group(2)

    # Faqat guruh adminlari uchun ishlaydi
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        return

    user = await get_user_by_login(login)
    if not user or not user.site_password_hash:
        return  # login topilmadi — indamaymiz (xato login ekanini oshkor qilmaslik uchun)

    password_matches = bcrypt.checkpw(
        password.encode("utf-8"), user.site_password_hash.encode("utf-8")
    )
    if not password_matches:
        return

    await link_group_to_user(login, message.chat.id)

    try:
        await (
            message.delete()
        )  # parol ochiq matnda qolib ketmasligi uchun xabarni o'chiramiz
    except Exception:
        pass

    from utils.keyboards import reports_keyboard

    await bot.send_message(
        message.chat.id,
        "✅ Guruh muvaffaqiyatli bog'landi!\n\n"
        "Bir login bilan cheksiz guruh bog'lash mumkin.\n"
        "Saytdagi o'zgarishlar barcha bog'langan guruhlarga yuboriladi.\n\n"
        "Hisobotlar uchun chap tomondagi <b>Menu</b> tugmasidan foydalaning yoki /menu bosing 👇",
        reply_markup=reports_keyboard(),
    )
