import logging
import re

import bcrypt
from aiogram import Router, F, Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import Message, ChatMemberUpdated, ReplyKeyboardRemove

from database.requests import get_user_by_login, link_group_to_user

router = Router(name="group")
logger = logging.getLogger(__name__)

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


def _check_password(raw_password: str, stored_hash: str | None) -> bool:
    """
    Parolni tekshiradi. Bcrypt hash bo'lsa — bcrypt bilan, aks holda
    (eski/plaintext hisoblar uchun) oddiy taqqoslash bilan tekshiradi.
    JS backend /api/login dagi mantiq bilan bir xil bo'lishi shart!
    """
    if not stored_hash:
        return False

    stored_hash = stored_hash.strip()

    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(
                raw_password.encode("utf-8"), stored_hash.encode("utf-8")
            )
        except (ValueError, TypeError) as e:
            # Bazadagi qiymat "$2a$" bilan boshlansa-da, yaroqsiz bcrypt
            # hash bo'lib chiqishi mumkin — bu holatda ham dastur qulamasin.
            logger.error("[group] bcrypt.checkpw xatosi (yaroqsiz hash): %s", e)
            return False

    # Plaintext parol (eski/qo'lda yaratilgan hisoblar uchun fallback)
    return raw_password == stored_hash


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

    try:
        # Faqat guruh adminlari uchun ishlaydi
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    except Exception as e:
        logger.error("[group] get_chat_member xatosi: %s", e)
        return

    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        logger.info(
            "[group] chat=%s user=%s admin emas, o'tkazib yuborildi",
            message.chat.id,
            message.from_user.id,
        )
        return

    user = await get_user_by_login(login)
    if not user:
        logger.info("[group] login topilmadi: %s (chat=%s)", login, message.chat.id)
        return  # login topilmadi — indamaymiz (xato login ekanini oshkor qilmaslik uchun)

    if not _check_password(password, user.site_password_hash):
        logger.info(
            "[group] parol mos kelmadi: login=%s (chat=%s)", login, message.chat.id
        )
        return

    await link_group_to_user(login, message.chat.id)
    logger.info(
        "[group] MUVAFFAQIYATLI bog'landi: login=%s chat_id=%s",
        login,
        message.chat.id,
    )

    try:
        await (
            message.delete()
        )  # parol ochiq matnda qolib ketmasligi uchun xabarni o'chiramiz
    except Exception:
        pass

    from utils.keyboards import reports_keyboard

    # Eski pastki (Reply) klaviatura hali ham a'zolar ekranida qolgan bo'lishi mumkin —
    # uni olib tashlash uchun avval bo'sh ReplyKeyboardRemove yuboramiz.
    try:
        cleanup = await bot.send_message(
            message.chat.id, "\u2063", reply_markup=ReplyKeyboardRemove()
        )
        await cleanup.delete()
    except Exception:
        pass

    await bot.send_message(
        message.chat.id,
        "✅ Guruh muvaffaqiyatli bog'landi!\n\n"
        "Bir login bilan cheksiz guruh bog'lash mumkin.\n"
        "Saytdagi o'zgarishlar barcha bog'langan guruhlarga yuboriladi.\n\n"
        "Hisobotlar uchun chap tomondagi <b>Menu</b> tugmasidan foydalaning yoki /menu bosing 👇",
        reply_markup=reports_keyboard(),
    )