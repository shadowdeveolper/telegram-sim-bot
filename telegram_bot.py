import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import requests
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PHONE_NUMBER = 0

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_1 = "@YourFirstChannel"  # Replace with your first channel username
CHANNEL_2 = "@YourSecondChannel"  # Replace with your second channel username
API_URL = "http://tmphpscripts.xyz/APIv14/index.php?num="

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = update.effective_chat.id

    channel1_status = await check_channel_membership(context, chat_id, CHANNEL_1)
    channel2_status = await check_channel_membership(context, chat_id, CHANNEL_2)

    if not channel1_status or not channel2_status:
        await update.message.reply_text(
            f"Please join both channels to continue:\n"
            f"1. {CHANNEL_1}: https://t.me/YourFirstChannel\n"
            f"2. {CHANNEL_2}: https://t.me/YourSecondChannel\n"
            f"After joining, type /start again."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Welcome, {user.first_name}! Please send the phone number to get SIM details."
    )
    return PHONE_NUMBER

async def check_channel_membership(context, chat_id, channel_username):
    try:
        member = await context.bot.get_chat_member(channel_username, chat_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking membership for {channel_username}: {e}")
        return False

async def get_sim_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_number = update.message.text.strip()

    if not phone_number.isdigit() or len(phone_number) < 10:
        await update.message.reply_text("Please send a valid phone number.")
        return PHONE_NUMBER

    try:
        response = requests.get(f"{API_URL}{phone_number}")
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                details = data[0]
                reply = (
                    f"**SIM Details**\n"
                    f"Mobile #: {details.get('Mobile #', 'N/A')}\n"
                    f"Name: {details.get('Name', 'N/A')}\n"
                    f"CNIC: {details.get('CNIC', 'N/A')}\n"
                    f"Address: {details.get('Address', 'N/A')}"
                )
            else:
                reply = "No details found for this number."
        else:
            reply = "Error fetching details. Please try again later."
    except Exception as e:
        logger.error(f"Error fetching API: {e}")
        reply = "Error connecting to the server. Please try again."

    await update.message.reply_text(reply)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again.")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sim_details)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
