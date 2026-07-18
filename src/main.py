import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes, PreCheckoutQueryHandler
from src.config import settings
from src.database.core import init_db

from src.handlers.start import start_command, verify_captcha
from src.handlers.profile import handle_profile, handle_main_channel, handle_support
from src.handlers.payment import (
    start_deposit, choose_currency, receive_amount, choose_method, 
    choose_crypto_coin, receive_screenshot, cancel_deposit, admin_deposit_action
)
from src.handlers.buy import (
    handle_demo, start_buy_groups, buy_choose_currency, buy_choose_method,
    buy_process_method, buy_receive_gc, buy_request_screenshot, buy_receive_screenshot, admin_buy_action,
    precheckout_callback, successful_payment_callback
)
from src.handlers.admin import start_broadcast, receive_broadcast, add_balance, remove_balance
from src.utils.states import *

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An unexpected error occurred. Our team has been notified.")
        except Exception:
            pass

async def post_init(application: Application):
    await init_db()
    logger.info("Bot and Database Initialization Complete.")

def main():
    app = Application.builder().token(settings.bot_token.get_secret_value()).post_init(post_init).build()
    
    app.add_error_handler(error_handler)
    nav_buttons_regex = "^(👤 Profile|🛒 Buy Groups|🎬 Demo|📢 Main Channel|💬 Contact Admin|💰 Deposit to Wallet)$"

    # Telegram Stars Payments Native Handlers
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # Admin Broadcast FSM
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_WAITING: [MessageHandler(~filters.COMMAND, receive_broadcast)]
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        per_message=False
    )
    app.add_handler(broadcast_handler)

    # Admin Balance Commands
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("removebalance", remove_balance))

    # Base Navigation Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(verify_captcha, pattern="^captcha_"))
    app.add_handler(MessageHandler(filters.Regex("^👤 Profile$"), handle_profile))
    app.add_handler(MessageHandler(filters.Regex("^📢 Main Channel$"), handle_main_channel))
    app.add_handler(MessageHandler(filters.Regex("^💬 Contact Admin$"), handle_support))
    app.add_handler(MessageHandler(filters.Regex("^🎬 Demo$"), handle_demo))
    
    # Admin Approval Handlers
    app.add_handler(CallbackQueryHandler(admin_buy_action, pattern="^buy_(app|rej)_"))
    app.add_handler(CallbackQueryHandler(admin_deposit_action, pattern="^admin_(approve|reject)_"))

    # Buy Groups FSM
    buy_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Buy Groups$"), start_buy_groups)],
        states={
            BUY_CHOOSING_CURRENCY: [CallbackQueryHandler(buy_choose_currency, pattern="^buy_sel_")],
            BUY_CHOOSING_METHOD: [CallbackQueryHandler(buy_choose_method, pattern="^buy_curr_")],
            BUY_GC_CODE: [
                CallbackQueryHandler(buy_process_method, pattern="^buy_meth_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(nav_buttons_regex), buy_receive_gc)
            ],
            BUY_SCREENSHOT: [
                CallbackQueryHandler(buy_request_screenshot, pattern="^buy_i_paid$"),
                MessageHandler(filters.PHOTO, buy_receive_screenshot)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_action$"),
            MessageHandler(filters.Regex(nav_buttons_regex), cancel_deposit)
        ],
        per_message=False
    )
    app.add_handler(buy_handler)

    # Deposit FSM
    deposit_handler = ConversationHandler(
        entry_points=[
            CommandHandler("deposit", start_deposit),
            MessageHandler(filters.Regex("^💰 Deposit to Wallet$"), start_deposit),
            CallbackQueryHandler(start_deposit, pattern="^start_deposit_flow$")
        ],
        states={
            CHOOSING_CURRENCY: [CallbackQueryHandler(choose_currency, pattern="^dep_curr_")],
            TYPING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(nav_buttons_regex), receive_amount)],
            CHOOSING_METHOD: [CallbackQueryHandler(choose_method, pattern="^dep_meth_")],
            CHOOSING_CRYPTO: [CallbackQueryHandler(choose_crypto_coin, pattern="^crypto_")],
            UPLOADING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_deposit),
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_action$"),
            MessageHandler(filters.Regex(nav_buttons_regex), cancel_deposit)
        ],
        per_message=False
    )
    app.add_handler(deposit_handler)

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
