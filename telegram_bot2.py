import logging
import asyncio
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import FastAPI
from telegram.error import TimedOut, NetworkError
from threading import Thread

# Aktivera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# Ditt Telegram-ID (Ägarens ID)
OWNER_ID = 7840233938  # Ersätt med ditt riktiga Telegram-ID

# Lagra användares bilder, videor och info
user_media = {}

# Rensa användares material vid start
def reset_user_media():
    global user_media
    user_media = {}

# Funktion för att hantera mottagna bilder och videor
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"{update.effective_user.first_name} {update.effective_user.last_name}" or "anonym"

    if user_id not in user_media:
        user_media[user_id] = {"photos": [], "videos": [], "chat_id": update.effective_chat.id, "counter": 0, "username": username}

    if update.message.photo:
        user_media[user_id]["photos"].append(update.message.photo[-1].file_id)
    elif update.message.video:
        user_media[user_id]["videos"].append(update.message.video.file_id)

    user_media[user_id]["counter"] += 1

    await update.message.reply_text(
        f"Tack, ditt material nummer {user_media[user_id]['counter']} har tagits emot!\n"
        "När du är klar med alla steg, skriv /send för att skicka allt material till kontrollanter."
    )

# Funktion för att skicka det insamlade materialet
async def send_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_media or (not user_media[user_id]["photos"] and not user_media[user_id]["videos"]):
        await update.message.reply_text("Du har inte skickat några bilder eller videor än!")
        return

    username = user_media[user_id]["username"]
    user_info_message = f"Användare: {username} (ID: {user_id}) har skickat följande material:\n"

    try:
        await context.bot.send_message(chat_id='-4662197024', text=user_info_message)
    except TimedOut:
        await update.message.reply_text("Timeout vid försök att skicka användarinformation. Försök igen.")
        return

    async def send_media_in_batches(media_list, media_type):
        batch_size = 10
        for i in range(0, len(media_list), batch_size):
            batch = media_list[i:i + batch_size]
            media_group = [
                InputMediaPhoto(media=file_id) if media_type == "photo" else InputMediaVideo(media=file_id)
                for file_id in batch
            ]
            try:
                await context.bot.send_media_group(chat_id='-4662197024', media=media_group)
                await asyncio.sleep(2)
            except TimedOut:
                await update.message.reply_text(f"Timeout vid försök att skicka {media_type}. Försöker igen...")
                await context.bot.send_media_group(chat_id='-4662197024', media=media_group)

    if user_media[user_id]["photos"]:
        await send_media_in_batches(user_media[user_id]["photos"], "photo")
    if user_media[user_id]["videos"]:
        await send_media_in_batches(user_media[user_id]["videos"], "video")

    try:
        await update.message.reply_text(
            "Tack för ditt bidrag, ditt material skickas vidare till gruppen. "
            "En av ägarna eller våra mod(s) kommer undersöka ditt material. "
            "Om du blir godkänd får du tillgång till gruppen inom 1-30 minuter.\n"
            "https://t.me/+cUeYDz-kov4zY2Q0"
        )
    except TimedOut:
        logger.warning(f"Timeout vid försök att skicka tackmeddelande till {user_id}")

    del user_media[user_id]

# Funktion för att skicka ett meddelande till en specifik användare (endast ägaren)
async def request_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Endast ägaren kan använda detta kommando.")
        return

    try:
        target_user_id = int(context.args[0])  # Användar-ID
        message_text = " ".join(context.args[1:])  # Meddelandet

        if not message_text:
            await update.message.reply_text("Du måste ange ett meddelande att skicka.")
            return

        await context.bot.send_message(chat_id=target_user_id, text=f"🔔 Meddelande från admin:\n\n{message_text}")
        await update.message.reply_text(f"Meddelandet har skickats till {target_user_id}.")

    except (IndexError, ValueError):
        await update.message.reply_text("Använd kommandot så här: `/requestchat <användar-ID> <meddelande>`")
    except TimedOut:
        await update.message.reply_text("Timeout vid försök att skicka meddelandet. Försök igen.")
    except Exception as e:
        await update.message.reply_text(f"Fel uppstod: {e}")

# Funktion för att starta botten
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "*Swedish Beauty*\n\n"
        "Hej! För att få tillgång till gruppen, följ dessa steg:\n\n"
        "1️⃣ Skicka en skärmdump som visar att du har delat gruppen.\n"
        "2️⃣ Skicka några bilder på ditt smygfoto material (bidrag krävs).\n"
        "3️⃣ Skriv /send när du är klar, så skickas materialet till vår kontrollgrupp.\n"
        "4️⃣ När vi granskat ditt material får du en länk till gruppen!\n\n"
        "⏳ *Det tar vanligtvis 1-30 minuter för att granskas.*\n\n"
        "Lycka till! 🎉"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Huvudfunktion för att köra botten
async def run_telegram_bot():
    bot_token = '7283501110:AAGOu2q8CDqucCR0-ozm2vgUzHKBw6R5_kw'  # Replace with your bot token

    reset_user_media()

    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_material))
    application.add_handler(CommandHandler("chat", request_chat))  # Lägger till requestchat
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

    await application.run_polling()

# Run Telegram bot in the same event loop as FastAPI
@app.on_event("startup")
async def on_startup():
    # Run the telegram bot in background
    asyncio.create_task(run_telegram_bot())

# FastAPI route for testing
@app.get("/")
async def root():
    return {"message": "Bot is running!"}

# Run FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
