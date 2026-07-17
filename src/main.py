import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from src.config import settings
from src.database.core import init_db
from src.handlers.payment import (
    start_deposit, choose_currency, receive_amount, choose_method, 
    choose_crypto_coin, receive_screenshot, cancel_deposit
)
from src.utils.states import *

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context):
    # Registration & Captcha logic goes here.
    await update.message.reply_text("Welcome to the Payment Bot. Use /deposit to add funds.")

async def post_init(application: Application):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Bot started successfully.")

def main():
    app = Application.builder().token(settings.bot_token.get_secret_value()).post_init(post_init).build()

    # Core Deposit Conversation Handler
    deposit_handler = ConversationHandler(
        entry_points=[CommandHandler("deposit", start_deposit)],
        states={
            CHOOSING_CURRENCY: [CallbackQueryHandler(choose_currency, pattern="^dep_curr_")],
            TYPING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount),
                CallbackQueryHandler(cancel_deposit, pattern="^cancel_deposit$")
            ],
            CHOOSING_METHOD: [CallbackQueryHandler(choose_method, pattern="^dep_meth_")],
            CHOOSING_CRYPTO: [CallbackQueryHandler(choose_crypto_coin, pattern="^crypto_")],
            UPLOADING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_deposit),
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_deposit$"),
            # Cancel automatically if user sends a different command while in deposit flow
            MessageHandler(filters.COMMAND, cancel_deposit)
        ],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(deposit_handler)

    # Note: Admin callback handlers (admin_approve_X, admin_reject_X) will be routed here via standard CallbackQueryHandlers.

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
  
