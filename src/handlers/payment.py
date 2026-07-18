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
    text = "❖ **𝗗𝗲𝗽𝗼𝘀𝗶𝘁 𝗙𝘂𝗻𝗱𝘀**\n──────────────────────\nPlease select your preferred currency."
    if update.message:
        await update.message.reply_text(text, reply_markup=PremiumUI.currency_selection(), parse_mode="Markdown")
    elif update.callback_query:
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
            "For security reasons, our UPI ID is provided privately.\n\n"
            "Click the button below to message the Admin. Just press **Send** when the chat opens, and the Admin will provide the UPI ID."
        )
        keyboard = [[InlineKeyboardButton("📲 Message Admin for UPI", url=upi_link)], PremiumUI.cancel_inline()]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        # FIXED: Return a waiting state instead of END so the Cancel button works
        return UPLOADING_SCREENSHOT 

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
            "⚠️ *Note: We only accept Indian Rupee (INR) Gift Cards.*\n\n"
            "📸 **Upload the screenshot of your purchased gift card and code below to continue.**"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return UPLOADING_SCREENSHOT

    elif method == "Crypto":
        text = "❖ **𝗦𝗲𝗹𝗲𝗰𝘁 𝗖𝗿𝘆𝗽𝘁𝗼𝗰𝘂𝗿𝗿𝗲𝗻𝗰𝘆**\n──────────────────────\nChoose your preferred coin:"
        await query.edit_message_text(text, reply_markup=PremiumUI.crypto_selection(), parse_mode="Markdown")
        return CHOOSING_CRYPTO

async def choose_crypto_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coin = query.data.split("_")[1]
    context.user_data['deposit_crypto_coin'] = coin
    
    # Load dynamically from environment variables
    addresses = {
        "USDT": settings.usdt_address,
        "BTC": settings.btc_address,
        "ETH": settings.eth_address,
        "SOL": settings.sol_address
    }
    address = addresses.get(coin, "Address not configured.")
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={address}"
    
    text = (
        f"❖ **{coin} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n"
        f"──────────────────────\n"
        f"📤 Send exactly `{context.user_data['deposit_amount']}` {context.user_data['deposit_currency']} to:\n\n"
        f"`{address}`\n*(Tap address to copy)*\n\n"
        f"[🖼️ Click here to view QR Code]({qr_url})\n\n"
        f"📸 **Upload your payment screenshot once complete.**"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown", disable_web_page_preview=False)
    return UPLOADING_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a valid photo/screenshot.")
        return UPLOADING_SCREENSHOT

    photo_file_id = update.message.photo[-1].file_id
    user = update.message.from_user
    amount = context.user_data['deposit_amount']
    currency = context.user_data['deposit_currency']
    method = context.user_data['deposit_method']
    coin = context.user_data.get('deposit_crypto_coin', '')

    async with AsyncSessionLocal() as session:
        new_tx = Transaction(user_id=user.id, amount=amount, currency=currency, method=method, crypto_coin=coin, screenshot_id=photo_file_id)
        session.add(new_tx)
        await session.commit()
        await session.refresh(new_tx)
        tx_id = new_tx.id

    admin_text = (f"🚨 **New Wallet Deposit**\n\n👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n"
                  f"💵 Amount: {amount} {currency}\n💳 Method: {method} {coin}\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{tx_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]]
    
    await context.bot.send_photo(chat_id=settings.owner_id, photo=photo_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ **Payment Proof Submitted.** Our team will verify it shortly.", parse_mode="Markdown", reply_markup=PremiumUI.main_menu())
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
                await query.edit_message_caption(caption=query.message.caption + "\n\n⚠️ STATUS: ALREADY PROCESSED")
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
                await query.edit_message_caption(caption=query.message.caption + "\n\n✅ STATUS: APPROVED & CREDITED")
                
            else:
                tx.status = "Rejected"
                await session.commit()
                try:
                    await context.bot.send_message(chat_id=tx.user_id, text="❌ **Deposit Rejected.**\nYour payment could not be verified.", parse_mode="Markdown")
                except Exception:
                    pass
                await query.edit_message_caption(caption=query.message.caption + "\n\n❌ STATUS: REJECTED")
                
    except Exception as e:
        logger.error(f"Admin Deposit Error: {e}")
        await query.edit_message_caption(caption=query.message.caption + "\n\n⚠️ PROCESSING ERROR")

async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "🚫 **Action Cancelled**\n──────────────────────\nYour process has been safely terminated."
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=PremiumUI.main_menu())
    return END
