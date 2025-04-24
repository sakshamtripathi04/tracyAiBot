import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from mistralai import Mistral
from dotenv import load_dotenv
import os
import logging
import re

# Set up logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Verify that keys are loaded
if not TELEGRAM_TOKEN or not MISTRAL_API_KEY:
    logger.error("TELEGRAM_TOKEN or MISTRAL_API_KEY not found in .env file")
    raise ValueError("Missing TELEGRAM_TOKEN or MISTRAL_API_KEY in .env file")

# Initialize Mistral client
client = Mistral(api_key=MISTRAL_API_KEY)

# Mistral API call with ownership handling
def get_mistral_response(message):
    try:
        # Define ownership-related keywords
        ownership_keywords = [
            r'who made you', r'who created you', r'who owns you', 
            r'creator', r'owner', r'who built you', r'your maker', 
            r'who developed you', r'who programmed you'
        ]
        
        # Check if the message contains ownership-related keywords (case-insensitive)
        is_ownership_query = any(re.search(keyword, message.lower()) for keyword in ownership_keywords)
        
        if is_ownership_query:
            logger.info("Detected ownership-related query")
            return "I'm Tracy, created by a team of 4 people in Greater Noida. Thanks to them for bringing me to life!"
        
        # For other queries, call Mistral API
        logger.info(f"Sending message to Mistral: {message}")
        chat_response = client.chat.complete(
            model="mistral-large-latest",  # Use the latest model; check docs for available models
            messages=[{"role": "user", "content": message}]  # Dictionary-based message
        )
        response = chat_response.choices[0].message.content
        logger.info("Received response from Mistral")
        # Replace any mention of Mistral AI with Tracy
        response = response.replace("Mistral AI", "Tracy")
        response = response.replace("Mistral", "Tracy")
        return response
    except Exception as e:
        logger.error(f"Mistral API error: {e}")
        return "Sorry, Tracy couldn't connect to the AI service. Please try again later."

# Telegram bot handlers
async def start(update, context):
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text("Hello! I'm Tracy, your friendly chatbot. Send me a message to get started!")

async def handle_message(update, context):
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_message}")
    mistral_response = get_mistral_response(user_message)
    await update.message.reply_text(mistral_response)

async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}")
    if update:
        await update.message.reply_text("Tracy encountered an error. Please try again.")

def main():
    try:
        # Use Application for v20.0+
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)
        
        logger.info("Starting Tracy bot polling...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start Tracy bot: {e}")
        raise

if __name__ == "__main__":
    main()
