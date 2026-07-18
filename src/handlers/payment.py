import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from src.utils.states import *
from src.config import settings
from src.database.models import Transaction, User
from src.database.core import AsyncSessionLocal
from sqlalchemy import select
from src.utils.keyboards import PremiumUI

logger = logging.getLogger(__name__)

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear() # Instantly reset any interrupted state
    text = "💰 **Deposit Funds**\nPlease select your preferred currency."
    
    if update.message:
        await update.message.reply_text(text, reply_markup=PremiumUI.currency_selection(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer() # FIXED: Prevents Telegram loading spinner freeze
        await update.callback_query.edit_message_text(text, reply_markup=PremiumUI.currency_selection(), parse_mode="Markdown")
    return CHOOSING_CURRENCY

async def choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    currency = query.data.split("_")[2]
    context.user_data['deposit_currency'] = currency
    
    text = f"❖ **𝗘𝗻𝘁𝗲𝗿 𝗔𝗺𝗼𝘂𝗻𝘁**\n──────────────────────\nCurrency selected: **{currency}**\n\n⌨️ Please type the amount you wish to deposit."
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
    return TYPING_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ **Invalid amount.** Please enter a valid positive number.")
        return TYPING_AMOUNT

    context.user_data['deposit_amount'] = amount
    text = f"❖ **𝗦𝗲𝗹𝗲𝗰𝘁 𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗠𝗲𝘁𝗵𝗼𝗱**\n──────────────────────\n💰 **Amount:** {amount} {context.user_data['deposit_currency']}\n\nSelect how you would like to pay:"
    await update.message.reply_text(text, reply_markup=PremiumUI.payment_methods(), parse_mode="Markdown")
    return CHOOSING_METHOD

async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.split("_")[2]
    context.user_data['deposit_method'] = method
    
    if method == "UPI":
        admin_username = settings.owner_username.replace('@', '')
        upi_link = f"https://t.me/{admin_username}?text=UPI"
        text = (
            "❖ **🏦 𝗨𝗣𝗜 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n"
            "──────────────────────\n"
            "Click the button below to message the Admin for UPI details.\n"
            "After paying, return here and click **I Paid**."
        )
        keyboard = [[InlineKeyboardButton("📲 Message Admin", url=upi_link)], [InlineKeyboardButton("✅ I Paid", callback_data="dep_i_paid")], PremiumUI.cancel_inline()]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return CONFIRM_PAYMENT

    elif method == "Amazon":
        currency = context.user_data['deposit_currency']
        amount = context.user_data['deposit_amount']
        if currency == "USD":
            amount = amount * settings.usd_to_inr_rate
            context.user_data['deposit_amount'] = amount
            context.user_data['deposit_currency'] = "INR"
            
        text = (
            "❖ **𝗔𝗺𝗮𝘇𝗼𝗻 𝗚𝗶𝗳𝘁 𝗖𝗮𝗿𝗱**\n"
            "──────────────────────\n"
            f"🛒 **Required:** ₹{amount} INR Gift Card\n\n"
            "⌨️ **Please send your Amazon Gift Card Code (INR) in this chat.**"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return RECEIVING_GC_CODE

    elif method == "Crypto":
        text = "🪙 **Select Cryptocurrency:**"
        await query.edit_message_text(text, reply_markup=PremiumUI.crypto_selection(prefix="dep_crypt"), parse_mode="Markdown")
        return CHOOSING_CRYPTO

async def receive_gc_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles receiving the GC Code as text before showing I Paid."""
    context.user_data['gc_code'] = update.message.text
    text = f"✅ **Code Received:** `{update.message.text}`\n\nPlease click **I Paid** to submit this code for verification, or **Cancel** to abort."
    await update.message.reply_text(text, reply_markup=PremiumUI.i_paid_keyboard("dep"), parse_mode="Markdown")
    return CONFIRM_PAYMENT

async def choose_crypto_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coin = query.data.split("_")[2]
    context.user_data['deposit_crypto_coin'] = coin
    
    addresses = {
        "USDT": settings.usdt_address,
        "BTC": settings.btc_address,
        "ETH": settings.eth_address,
        "SOL": settings.sol_address
    }
    address = addresses.get(coin, "Address not configured.")
    
    text = (f"❖ **{coin} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n──────────────────────\n"
            f"📤 Send exactly `{context.user_data['deposit_amount']}` {context.user_data['deposit_currency']} to:\n\n"
            f"`{address}`\n\nOnce transferred, click **I Paid**.")
    await query.edit_message_text(text, reply_markup=PremiumUI.i_paid_keyboard("dep"), parse_mode="Markdown")
    return CONFIRM_PAYMENT

async def ask_for_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = context.user_data.get('deposit_method', '')

    if method == "Amazon":
        # Direct submission, no screenshot required for GC.
        user = update.effective_user
        amount = context.user_data['deposit_amount']
        currency = context.user_data['deposit_currency']
        gc_code = context.user_data.get('gc_code', '')

        async with AsyncSessionLocal() as session:
            new_tx = Transaction(user_id=user.id, amount=amount, currency=currency, method=method, screenshot_id=None)
            session.add(new_tx)
            await session.commit()
            await session.refresh(new_tx)
            tx_id = new_tx.id

        admin_text = (f"🚨 **New Wallet Deposit (Amazon GC)**\n\n👤 {user.full_name} (@{user.username})\n🆔 `{user.id}`\n"
                      f"💵 {amount} {currency}\n💳 {method}\n🎟️ Code: `{gc_code}`\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]]
        
        await context.bot.send_message(chat_id=settings.owner_id, text=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            
        await query.edit_message_text("✅ **Gift Card Code Submitted.** Verification in progress.", parse_mode="Markdown")
        context.user_data.clear()
        return END

    else:
        # Crypto and UPI require Screenshot
        await query.edit_message_text("📸 **Upload your payment screenshot below:**", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return UPLOADING_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a valid photo/screenshot.")
        return UPLOADING_SCREENSHOT

    user = update.message.from_user
    amount = context.user_data['deposit_amount']
    currency = context.user_data['deposit_currency']
    method = context.user_data['deposit_method']
    coin = context.user_data.get('deposit_crypto_coin', '')
    photo_file_id = update.message.photo[-1].file_id
    
    async with AsyncSessionLocal() as session:
        new_tx = Transaction(user_id=user.id, amount=amount, currency=currency, method=method, crypto_coin=coin, screenshot_id=photo_file_id)
        session.add(new_tx)
        await session.commit()
        await session.refresh(new_tx)
        tx_id = new_tx.id

    admin_text = (f"🚨 **New Wallet Deposit (Screenshot)**\n\n👤 {user.full_name} (@{user.username})\n🆔 `{user.id}`\n"
                  f"💵 {amount} {currency}\n💳 {method} {coin}\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]]
    await context.bot.send_photo(chat_id=settings.owner_id, photo=photo_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    await update.message.reply_text("✅ **Payment Proof Submitted.** Verification in progress.", parse_mode="Markdown", reply_markup=PremiumUI.main_menu())
    context.user_data.clear()
    return END

async def admin_deposit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        action = query.data.split("_")[1]
        tx_id = int(query.data.split("_")[2])
        
        async with AsyncSessionLocal() as session:
            tx = await session.get(Transaction, tx_id)
            if not tx or tx.status != 'Pending':
                if query.message.photo:
                    await query.edit_message_caption(caption=query.message.caption + "\n\n⚠️ STATUS: ALREADY PROCESSED")
                else:
                    await query.edit_message_text(text=query.message.text + "\n\n⚠️ STATUS: ALREADY PROCESSED")
                return

            if action == "approve":
                tx.status = "Approved"
                user = await session.execute(select(User).where(User.telegram_id == tx.user_id))
                db_user = user.scalar_one_or_none()
                if db_user:
                    if tx.currency == "INR":
                        db_user.balance_inr += tx.amount
                    else:
                        db_user.balance_usd += tx.amount
                await session.commit()
                
                try:
                    await context.bot.send_message(chat_id=tx.user_id, text=f"✅ **Deposit Approved!**\n{tx.amount} {tx.currency} has been added to your wallet.", parse_mode="Markdown")
                except Exception:
                    pass
                
                if query.message.photo:
                    await query.edit_message_caption(caption=query.message.caption + "\n\n✅ STATUS: APPROVED & CREDITED")
                else:
                    await query.edit_message_text(text=query.message.text + "\n\n✅ STATUS: APPROVED & CREDITED")
                    
            else:
                tx.status = "Rejected"
                await session.commit()
                try:
                    await context.bot.send_message(chat_id=tx.user_id, text="❌ **Deposit Rejected.**\nYour payment could not be verified.", parse_mode="Markdown")
                except Exception:
                    pass
                
                if query.message.photo:
                    await query.edit_message_caption(caption=query.message.caption + "\n\n❌ STATUS: REJECTED")
                else:
                    await query.edit_message_text(text=query.message.text + "\n\n❌ STATUS: REJECTED")
                
    except Exception as e:
        logger.error(f"Admin Deposit Error: {e}")

async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🚫 **Action Cancelled**"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=PremiumUI.main_menu())
    return END
