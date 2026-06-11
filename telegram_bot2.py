import os
import asyncio
import aiosqlite
from urllib.parse import quote
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
REWARD_GROUP_ID = int(os.getenv("REWARD_GROUP_ID", "0"))
REQUIRED_INVITES = int(os.getenv("REQUIRED_INVITES", "3"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
DB = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            invited_by INTEGER,
            rewarded INTEGER DEFAULT 0
        )
        """)

        cur = await db.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cur.fetchall()]

        if "reward_link" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN reward_link TEXT")

        await db.commit()


def referral_link(user_id: int):
    return f"https://t.me/{BOT_USERNAME}?start={user_id}"


async def invite_count(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE invited_by = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row[0]


async def is_rewarded(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT rewarded FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row and row[0] == 1


async def share_keyboard(user_id: int):
    count = await invite_count(user_id)
    link = referral_link(user_id)

    share_text = (
        "Bästa smygfoto gruppen har öppnats igen, sjukt material du vill ej missa 👀\n\n"
        "Den bästa gratis-inträde Telegram grupp som finns!\n\n"
        "Joina via min personliga länk"
    )

    share_url = (
        f"https://t.me/share/url?"
        f"url={quote(link)}&text={quote(share_text)}"
    )

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📤 Dela — {count}/{REQUIRED_INVITES} mot Gratis Access",
            url=share_url
        )]
    ])


async def send_panel(user_id: int):
    count = await invite_count(user_id)
    left = max(REQUIRED_INVITES - count, 0)
    link = referral_link(user_id)

    await bot.send_message(
        user_id,
        "🔥 Smygfoto Inträde 🔥\n\n"
        f"📊 Du har {count} invites\n"
        f"🎯 Bara {left} kvar till nästa belöning: 🔓 Gratis Access!\n\n"
        "🎁 BELÖNING:\n"
        f"🔒 {REQUIRED_INVITES} invites — 🔓 Gratis Access\n\n"
        f"📎 Din personliga invite-länk:\n{link}",
        reply_markup=await share_keyboard(user_id)
    )


async def create_one_time_group_link(user_id: int):
    invite_link = await bot.create_chat_invite_link(
        chat_id=REWARD_GROUP_ID,
        name=f"Reward {user_id}",
        member_limit=1
    )
    return invite_link.invite_link


async def reward_if_ready(user_id: int):
    count = await invite_count(user_id)

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT rewarded, reward_link FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()

        if not row:
            return

        rewarded, existing_link = row

        if rewarded == 1 and existing_link:
            return

        if count >= REQUIRED_INVITES:
            try:
                one_time_link = await create_one_time_group_link(user_id)

                await db.execute(
                    "UPDATE users SET rewarded = 1, reward_link = ? WHERE user_id = ?",
                    (one_time_link, user_id)
                )
                await db.commit()

                print(f"[REWARD] User {user_id} låste upp grupp-länken")

                await bot.send_message(
                    user_id,
                    "🎉 Grattis!\n\n"
                    f"Du har nått {REQUIRED_INVITES} invites och låst upp Gratis Access.\n\n"
                    "🔐 Här är din personliga grupp-länk:\n"
                    f"{one_time_link}\n\n"
                    "⚠️ VIKTIGT:\n"
                    "Den här länken är personlig och fungerar bara för 1 person.\n"
                    "Dela inte länken med någon annan.\n"
                    "Om någon annan använder den först kommer du inte kunna använda den själv."
                )

            except Exception as e:
                print("KUNDE INTE SKAPA GRUPPLÄNK:", repr(e))
                await bot.send_message(
                    user_id,
                    "⚠️ Du har nått dina invites, men jag kunde inte skapa grupp-länken.\n\n"
                    "Kontrollera att botten är admin i reward-gruppen och har rätt att skapa invite-länkar."
                )


async def notify_inviter(inviter_id: int, new_user):
    count = await invite_count(inviter_id)
    left = max(REQUIRED_INVITES - count, 0)

    username = f"@{new_user.username}" if new_user.username else "inget username"

    print(
        f"[NY INVITE] Inviter ID: {inviter_id} | "
        f"Ny användare: {new_user.full_name} | "
        f"Username: {username} | "
        f"Totalt invites: {count}/{REQUIRED_INVITES}"
    )

    await bot.send_message(
        inviter_id,
        f"🎉 Ny invite!\n\n"
        f"👤 {new_user.full_name} gick med via din länk.\n"
        f"📊 Totalt invites: {count}/{REQUIRED_INVITES}\n"
        f"🎯 Kvar till Gratis Access: {left}"
    )

    await send_panel(inviter_id)


@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    invited_by = None

    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != user_id:
                invited_by = ref_id
        except ValueError:
            pass

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )
        exists = await cur.fetchone()

        if not exists:
            await db.execute(
                "INSERT INTO users (user_id, invited_by, rewarded) VALUES (?, ?, 0)",
                (user_id, invited_by)
            )
            await db.commit()

            if invited_by:
                if not await is_rewarded(invited_by):
                    await notify_inviter(invited_by, message.from_user)
                    await reward_if_ready(invited_by)

    await send_panel(user_id)
    await reward_if_ready(user_id)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN saknas i .env")

    if not BOT_USERNAME:
        raise ValueError("BOT_USERNAME saknas i .env")

    if not REWARD_GROUP_ID:
        raise ValueError("REWARD_GROUP_ID saknas i .env")

    await init_db()
    print("Botten är igång...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
