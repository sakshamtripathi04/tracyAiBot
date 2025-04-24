import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from mistralai.client import MistralClient
from dotenv import load_dotenv
from flask import Flask
import os
import logging
import re
import threading

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not TELEGRAM_TOKEN or not MISTRAL_API_KEY:
    logger.error("Missing TELEGRAM_TOKEN or MISTRAL_API_KEY")
    raise ValueError("Missing required environment variables")

# Initialize Mistral client
client = MistralClient(api_key=MISTRAL_API_KEY)

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Bot is running!"

def get_mistral_response(message):
    try:
        ownership_keywords = [
            r'who made you', r'who created you', r'who owns you', 
            r'creator', r'owner', r'who built you', r'your maker', 
            r'who developed you', r'who programmed you'
        ]
        is_ownership_query = any(re.search(keyword, message.lower()) for keyword in ownership_keywords)
        if is_ownership_query:
            logger.info("Detected ownership-related query")
            return "I'm Tracy, created by Team of 4 People At Grater Noida. Thanks to them for bringing me to life!"
        logger.info(f"Sending message to Mistral: {message}")
        chat_response = client.chat(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": message}]
        )
        response = chat_response.choices[0].message.content
        logger.info("Received response from Mistral")
        response = response.replace("Mistral AI", "Tracy AI").replace("Mistral", "Tracy")
        return response
    except Exception as e:
        logger.error(f"Mistral API error: {e}")
        return "Sorry, Tracy couldn't connect to the AI service. Please try again later."

async def start(update, context):
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text("Hello! I'm Tracy, your friendly chatbot created by IILM students. Send me a message to get started!")

async def handle_message(update, context):
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_message}")
    mistral_response = get_mistral_response(user_message)
    await update.message.reply_text(mistral_response)

async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}")
    if update:
        await update.message.reply_text("Tracy encountered an error. Please try again.")

def run_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    logger.info("Starting Tracy bot polling...")
    application.run_polling()

if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))))
    flask_thread.daemon = True
    flask_thread.start()
    # Start the bot
    run_bot()
