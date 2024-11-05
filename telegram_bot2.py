import os
import logging
import asyncio
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Dummy route to keep the server alive
@app.route('/')
def home():
    return "Bot is running!"

# Store user media
user_media = {}

# Function to handle received media
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    if not username:
        username = f"{first_name} {last_name}" if first_name or last_name else "anonym"
    
    if user_id not in user_media:
        user_media[user_id] = {"photos": [], "videos": [], "chat_id": update.effective_chat.id, "counter": 0}

    if update.message.photo:
        user_media[user_id]["photos"].append(update.message.photo[-1].file_id)
        user_media[user_id]["counter"] += 1
    elif update.message.video:
        user_media[user_id]["videos"].append(update.message.video.file_id)
        user_media[user_id]["counter"] += 1

    await update.message.reply_text(f"Tack, ditt material nummer {user_media[user_id]['counter']} har tagits emot!\nNär du är klar, skriv /send för att skicka allt material till gruppen.")

# Function to send collected media
async def send_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    if not username:
        username = f"{first_name} {last_name}" if first_name or last_name else "anonym"
    
    if user_id not in user_media or (not user_media[user_id]["photos"] and not user_media[user_id]["videos"]):
        await update.message.reply_text("Du har inte skickat några bilder eller videor än!")
        return

    user_info_message = f"Användare: {username} (ID: {user_id}) har skickat följande material:\n"
    media_group = []
    for photo_id in user_media[user_id]["photos"]:
        media_group.append(InputMediaPhoto(media=photo_id))
    for video_id in user_media[user_id]["videos"]:
        media_group.append(InputMediaVideo(media=video_id))

    await context.bot.send_message(chat_id='-1002287795140', text=user_info_message)
    await context.bot.send_media_group(chat_id='-1002287795140', media=media_group)

    thank_you_message = (
        "Tack för ditt bidrag, ditt material skickas vidare till gruppen. "
        "En av ägarna eller våra mod(s) kommer undersöka ditt material. "
        "Om du blir godkänd får du tillgång till gruppen. "
        "Så länge kan du ansöka att komma in i gruppen så godkänns du när materialet har godkänts!\n\n"
        "https://t.me/+VHQKGrUi2K44ZDdh"
    )
    
    await update.message.reply_text(thank_you_message)
    del user_media[user_id]

# Start bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "*LION BAR FC*\n\n"
        "Hej, tack för ditt intresse att få tillgång till gruppen!\n\n"
        "*VIKTIGT INFOMRATION*\n\n"
        "Efter du blivit godkänt till gruppen, var vänligen att skicka ditt material till gruppen, "
        "så att du kan säkerhetsställa du inte blir kickad i rensningen och så att nytt material kommer in i gruppen!\n\n"
        "*Hur kommer jag in?*\n\n"
        "*Var vänligen skicka minst 3-5 bilder eller videor!*\n\n"
        "När du är klar, skriv /send för att skicka allt material till vår kontroll grupp, så vi kan ge dig tillgång!"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Run bot
async def run_bot():
    bot_token = '7484300801:AAG11ALjQTCZqXJz-mk5E4vnhqPx_vJtm6A'
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_material))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

    # Start bot polling
    await application.run_polling()

# Start Flask in a separate thread
def start_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Main function to run both Flask and Telegram bot
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Use asyncio's new event loop for the Telegram bot to avoid conflicts with Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())
    loop.run_forever()
