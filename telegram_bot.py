import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Aktivera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lagra användares bilder och info
user_images = {}

# Funktion för att hantera mottagna bilder
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id

    # Skapa en ny lista för användaren om den inte finns
    if user_id not in user_images:
        user_images[user_id] = {"images": [], "chat_id": chat_id}

    # Lägga till bilden till listan
    user_images[user_id]["images"].append(update.message.photo[-1].file_id)

    # Kontrollera om användaren har skickat tillräckligt med bilder
    if len(user_images[user_id]["images"]) >= 3:
        # Skicka vidare bilderna till gruppen
        media_group = [InputMediaPhoto(media=file_id) for file_id in user_images[user_id]["images"]]
        
        await context.bot.send_media_group(
            chat_id='-4583748308',  # Din grupps chat_id med minus
            media=media_group
        )
        
        # Skicka tackmeddelande till användaren
        thank_you_message = (
            "Tack för ditt bidrag, dina bilder skickas vidare till gruppen. "
            "En av ägarna eller våra mod(s) kommer undersöka ditt material. "
            "Om du blir godkänd får du tillgång till gruppen. "
            "Så länge kan du ansöka att komma in i gruppen så godkänns du när materialet har godkänts!\n\n"
            "https://t.me/+VHQKGrUi2K44ZDdh"
        )
        
        await update.message.reply_text(thank_you_message)

        # Rensa bilderna från minnet efter att de skickats
        del user_images[user_id]

# Funktion för att starta botten
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "*LION BAR FC*\n\n"
        "Hej, tack för ditt intresse att få tillgång till gruppen!\n\n"
        "*VIKTIGT INFOMRATION*\n\n"
        "Efter du blivit godkänt till gruppen, var vänligen att skicka ditt material till gruppen, "
        "så att du kan säkerhetsställa du inte blir kickad i rensningen och så att nytt material kommer in i gruppen!\n\n"
        "*Hur kommer jag in?*\n\n"
        "Var vänligen skicka 3-5 bilder:"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Huvudfunktion för att köra botten
def main():
    bot_token = '7484300801:AAG11ALjQTCZqXJz-mk5E4vnhqPx_vJtm6A'  # Din bot-token
    application = ApplicationBuilder().token(bot_token).build()

    # Registrera kommandon och meddelandehanterare
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()

if __name__ == '__main__':
    main()
