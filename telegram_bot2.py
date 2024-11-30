import logging
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Aktivera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lagra användares bilder, videor och info
user_media = {}

# Funktion för att hantera mottagna bilder och videor
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username  # Hämtar användarnamnet
    first_name = update.effective_user.first_name  # Hämtar förnamnet
    last_name = update.effective_user.last_name  # Hämtar efternamnet

    # Om ingen användarnamn finns, skapa ett namn baserat på förnamn och efternamn
    if not username:
        username = f"{first_name} {last_name}" if first_name or last_name else "anonym"
    
    # Skapa en ny lista för användaren om den inte finns
    if user_id not in user_media:
        user_media[user_id] = {"photos": [], "videos": [], "chat_id": update.effective_chat.id, "counter": 0}

    # Kontrollera om meddelandet innehåller en bild eller video
    if update.message.photo:
        user_media[user_id]["photos"].append(update.message.photo[-1].file_id)
        user_media[user_id]["counter"] += 1
    elif update.message.video:
        user_media[user_id]["videos"].append(update.message.video.file_id)
        user_media[user_id]["counter"] += 1

    # Skicka ett tackmeddelande efter varje material och påminn om /send
    await update.message.reply_text(f"Tack, ditt material nummer {user_media[user_id]['counter']} har tagits emot!\nNär du är klar, skriv /send för att skicka allt material till gruppen.")

# Funktion för att skicka det insamlade materialet
async def send_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username  # Hämtar användarnamnet
    first_name = update.effective_user.first_name  # Hämtar förnamnet
    last_name = update.effective_user.last_name  # Hämtar efternamnet

    # Om ingen användarnamn finns, skapa ett namn baserat på förnamn och efternamn
    if not username:
        username = f"{first_name} {last_name}" if first_name or last_name else "anonym"
    
    # Kontrollera om användaren har skickat några bilder eller videor
    if user_id not in user_media or (not user_media[user_id]["photos"] and not user_media[user_id]["videos"]):
        await update.message.reply_text("Du har inte skickat några bilder eller videor än!")
        return

    # Skapa en meddelande som inkluderar användarens ID och namn
    user_info_message = f"Användare: {username} (ID: {user_id}) har skickat följande material:\n"

    # Skapa en lista för alla media att skicka (bilder + videor)
    media_group = []
    for photo_id in user_media[user_id]["photos"]:
        media_group.append(InputMediaPhoto(media=photo_id))
    for video_id in user_media[user_id]["videos"]:
        media_group.append(InputMediaVideo(media=video_id))

    # Skicka vidare materialet till gruppen
    await context.bot.send_message(
        chat_id='-1002273687711',  # Din grupps chat_id med minus
        text=user_info_message,
    )
    
    await context.bot.send_media_group(
        chat_id='-1002273687711',
        media=media_group
    )

    # Skicka tackmeddelande till användaren
    thank_you_message = (
        "Tack för ditt bidrag, ditt material skickas vidare till gruppen. "
        "En av ägarna eller våra mod(s) kommer undersöka ditt material. "
        "Om du blir godkänd får du tillgång till gruppen.\n"
        "t.me/2fEGCLjXZFkwYTA0"
    )
    
    await update.message.reply_text(thank_you_message)

    # Rensa materialet från minnet efter att det skickats
    del user_media[user_id]

# Funktion för att starta botten
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

# Huvudfunktion för att köra botten
def main():
    bot_token = '7463217999:AAHXZzQg0LhewuF0w0OUjsDCyVQ1EhlhvJg'  # Din bot-token
    application = ApplicationBuilder().token(bot_token).build()

    # Registrera kommandon och meddelandehanterare
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_material))  # Kommando för att skicka materialet
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

    application.run_polling()

if __name__ == '__main__':
    main()
