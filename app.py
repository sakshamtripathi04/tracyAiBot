import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from mistralai import Mistral
from dotenv import load_dotenv
from flask import Flask, request
import os
import logging
import asyncio

# Set up logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Access environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Verify that keys are loaded
if not TELEGRAM_TOKEN or not MISTRAL_API_KEY or not WEBHOOK_URL:
    logger.error("TELEGRAM_TOKEN, MISTRAL_API_KEY, or WEBHOOK_URL not found")
    raise ValueError("Missing TELEGRAM_TOKEN, MISTRAL_API_KEY, or WEBHOOK_URL")

# Initialize Mistral client
client = Mistral(api_key=MISTRAL_API_KEY)

# Initialize Telegram application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Mistral API call
def get_mistral_response(message):
    try:
        logger.info(f"Sending message to Mistral: {message}")
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": message}]
        )
        response = chat_response.choices[0].message.content
        logger.info("Received response from Mistral")
        return response
    except Exception as e:
        logger.error(f"Mistral API error: {e}")
        return "Sorry, I couldn't connect to the AI service. Please try again later."

# Telegram bot handlers
async def start(update, context):
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text("Hello! I'm your chatbot powered by Tracy AI. Send me a message!")

async def handle_message(update, context):
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_message}")
    mistral_response = get_mistral_response(user_message)
    await update.message.reply_text(mistral_response)

async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}")
    if update:
        await update.message.reply_text("An error occurred. Please try again.")

# Flask route for Telegram webhook
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return {"status": "ok"}, 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}, 500

@app.route("/")
def home():
    return "Telegram Bot is running!"

async def set_webhook():
    try:
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")
        logger.info("Webhook set successfully")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

def main():
    try:
        # Add handlers to application
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)

        # Run Flask app and set webhook
        loop = asyncio.get_event_loop()
        loop.run_until_complete(set_webhook())
        logger.info("Starting Flask app...")
        app.run(host="0.0.0.0", port=PORT, debug=False)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
