import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from src.config import settings
from src.database.core import init_db

from src.handlers.start import start_command, verify_captcha
from src.handlers.profile import handle_profile, handle_coming_soon
from src.handlers.payment import (
    start_deposit, choose_currency, receive_amount, choose_method, 
    choose_crypto_coin, receive_screenshot, cancel_deposit
)
from src.utils.states import *

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await init_db()
    logger.info("Bot started successfully.")

def main():
    app = Application.builder().token(settings.bot_token.get_secret_value()).post_init(post_init).build()

    # Core Navigation Handlers (Triggered by Reply Keyboard Text)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(verify_captcha, pattern="^captcha_"))
    
    app.add_handler(MessageHandler(filters.Regex("^👤 Profile$"), handle_profile))
    app.add_handler(MessageHandler(filters.Regex("^(🛒 Purchase|👛 Wallet|🎁 Referral|📜 History|📢 Channel|🎧 Support)$"), handle_coming_soon))

    # Deposit FSM Flow
    deposit_handler = ConversationHandler(
        entry_points=[
            CommandHandler("deposit", start_deposit),
            MessageHandler(filters.Regex("^💰 Deposit$"), start_deposit)
        ],
        states={
            CHOOSING_CURRENCY: [CallbackQueryHandler(choose_currency, pattern="^dep_curr_")],
            TYPING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)
            ],
            CHOOSING_METHOD: [CallbackQueryHandler(choose_method, pattern="^dep_meth_")],
            CHOOSING_CRYPTO: [CallbackQueryHandler(choose_crypto_coin, pattern="^crypto_")],
            UPLOADING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_deposit),
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_action$"),
            MessageHandler(filters.Regex("^(👤 Profile|🛒 Purchase|👛 Wallet|🎁 Referral|📜 History|📢 Channel|🎧 Support|💰 Deposit)$"), cancel_deposit)
        ],
        per_message=False
    )

    app.add_handler(deposit_handler)

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
