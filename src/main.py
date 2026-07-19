import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes, PreCheckoutQueryHandler
from src.config import settings
from src.database.core import init_db

from src.handlers.start import start_command, verify_captcha
from src.handlers.profile import handle_profile, handle_main_channel, handle_support
from src.handlers.payment import (
    start_deposit, choose_currency, receive_amount, choose_method, 
    choose_crypto_coin, receive_gc_code, ask_for_proof, receive_screenshot, cancel_deposit, admin_deposit_action
)
from src.handlers.buy import (
    handle_demo, demo_select_callback, start_buy_groups, buy_selection_handler, buy_option_handler,
    buy_choose_currency, buy_process_method, buy_crypto_coin_selected, 
    buy_receive_gc_code, buy_ask_proof, buy_receive_proof, admin_buy_action
)
from src.handlers.admin import start_broadcast, receive_broadcast, add_balance, remove_balance
from src.utils.states import *
from src.groups_config import GROUPS
from src.database.models import User, Transaction
from src.database.core import AsyncSessionLocal
from sqlalchemy import select

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An unexpected error occurred.")
        except Exception:
            pass

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_") or query.invoice_payload.startswith("dep_stars_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    user = update.effective_user

    if payload.startswith("buy_"):
        parts = payload.split("_")
        group_id = parts[1]
        group = GROUPS[group_id]
        async with AsyncSessionLocal() as session:
            db_user = await session.get(User, user.id)
            if db_user: db_user.total_purchases += 1
            new_tx = Transaction(user_id=user.id, amount=payment.total_amount, currency=payment.currency, method="Stars", status="Approved")
            session.add(new_tx)
            await session.commit()
        try:
            invite = await context.bot.create_chat_invite_link(chat_id=group["chat_id"], member_limit=1, name=f"Stars_{user.id}")
            await update.message.reply_text(f"✅ **Payment Successful!**\n\nYour access link for **{group['name']}**:\n{invite.invite_link}\n\n⚠️ *Single-use only.*", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Stars Invite Link Error: {e}")
            await update.message.reply_text("✅ Payment successful, but we couldn't generate the invite link. Contact Admin.")

    elif payload.startswith("dep_stars_"):
        parts = payload.split("_")
        amount = float(parts[2])
        currency = parts[3]
        async with AsyncSessionLocal() as session:
            db_user = await session.get(User, user.id)
            if db_user:
                if currency == "INR": db_user.balance_inr += amount
                else: db_user.balance_usd += amount
                new_tx = Transaction(user_id=user.id, amount=amount, currency=currency, method="Stars", status="Approved")
                session.add(new_tx)
                await session.commit()
        await update.message.reply_text("✅ **Payment received successfully!** Your wallet has been credited.")

async def post_init(application: Application):
    await init_db()
    logger.info("Bot Ready.")

def main():
    app = Application.builder().token(settings.bot_token.get_secret_value()).post_init(post_init).build()
    app.add_error_handler(error_handler)
    
    nav_buttons_regex = "^(👤 Profile|🛒 Buy Groups|🎬 Demo|📢 Main Channel|💬 Contact Admin|💰 Deposit to Wallet)$"

    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("removebalance", remove_balance))

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(verify_captcha, pattern="^captcha_"))
    app.add_handler(MessageHandler(filters.Regex("^👤 Profile$"), handle_profile))
    app.add_handler(MessageHandler(filters.Regex("^📢 Main Channel$"), handle_main_channel))
    app.add_handler(MessageHandler(filters.Regex("^💬 Contact Admin$"), handle_support))
    app.add_handler(MessageHandler(filters.Regex("^🎬 Demo$"), handle_demo))
    app.add_handler(CallbackQueryHandler(demo_select_callback, pattern="^demo_sel_"))

    app.add_handler(CallbackQueryHandler(admin_buy_action, pattern="^buy_(app|rej)_"))
    app.add_handler(CallbackQueryHandler(admin_deposit_action, pattern="^admin_(approve|reject)_"))

    buy_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Buy Groups$"), start_buy_groups)],
        states={
            BUY_CHOOSING_OPTION: [CallbackQueryHandler(buy_selection_handler, pattern="^buy_sel_")],
            BUY_ROUTING: [CallbackQueryHandler(buy_option_handler, pattern="^buy_opt_")],
            BUY_CHOOSING_CURRENCY: [CallbackQueryHandler(buy_choose_currency, pattern="^buy_curr_")],
            BUY_CHOOSING_METHOD: [CallbackQueryHandler(buy_process_method, pattern="^buy_meth_")],
            BUY_CHOOSING_CRYPTO: [CallbackQueryHandler(buy_crypto_coin_selected, pattern="^buy_crypt_")],
            BUY_RECEIVING_GC_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(nav_buttons_regex), buy_receive_gc_code)],
            BUY_CONFIRM_PAYMENT: [CallbackQueryHandler(buy_ask_proof, pattern="^buy_i_paid$")],
            BUY_SCREENSHOT: [MessageHandler(filters.PHOTO & ~filters.COMMAND, buy_receive_proof)]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_action$"), 
            MessageHandler(filters.Regex(nav_buttons_regex), cancel_deposit),
            CallbackQueryHandler(start_deposit, pattern="^start_deposit_flow$")
        ],
        per_message=False,
        allow_reentry=True
    )
    app.add_handler(buy_handler)

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
            CHOOSING_CRYPTO: [CallbackQueryHandler(choose_crypto_coin, pattern="^dep_crypt_")],
            RECEIVING_GC_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(nav_buttons_regex), receive_gc_code)],
            CONFIRM_PAYMENT: [CallbackQueryHandler(ask_for_proof, pattern="^dep_i_paid$")],
            UPLOADING_SCREENSHOT: [MessageHandler(filters.PHOTO & ~filters.COMMAND, receive_screenshot)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_deposit),
            CallbackQueryHandler(cancel_deposit, pattern="^cancel_action$"),
            MessageHandler(filters.Regex(nav_buttons_regex), cancel_deposit),
            CallbackQueryHandler(start_deposit, pattern="^start_deposit_flow$")
        ],
        per_message=False,
        allow_reentry=True
    )
    app.add_handler(deposit_handler)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
