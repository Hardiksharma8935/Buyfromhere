from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.utils.states import *
from src.config import settings
from src.database.models import Transaction
from src.database.core import AsyncSessionLocal
from src.utils.keyboards import PremiumUI

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❖ **𝗗𝗲𝗽𝗼𝘀𝗶𝘁 𝗙𝘂𝗻𝗱𝘀**\n"
        "──────────────────────\n"
        "Please select your preferred currency for this transaction."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=PremiumUI.currency_selection(), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=PremiumUI.currency_selection(), parse_mode="Markdown")
    return CHOOSING_CURRENCY

async def choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    currency = query.data.split("_")[2]
    context.user_data['deposit_currency'] = currency
    
    text = (
        f"❖ **𝗘𝗻𝘁𝗲𝗿 𝗔𝗺𝗼𝘂𝗻𝘁**\n"
        f"──────────────────────\n"
        f"Currency selected: **{currency}**\n\n"
        f"⌨️ Please type the amount you wish to deposit."
    )
    
    keyboard = InlineKeyboardMarkup([PremiumUI.back_button("menu_deposit")])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    return TYPING_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ **Invalid amount.** Please enter a valid number.")
        return TYPING_AMOUNT

    context.user_data['deposit_amount'] = amount
    
    text = (
        f"❖ **𝗦𝗲𝗹𝗲𝗰𝘁 𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗠𝗲𝘁𝗵𝗼𝗱**\n"
        f"──────────────────────\n"
        f"💰 **Amount:** {amount} {context.user_data['deposit_currency']}\n\n"
        f"Select how you would like to pay:"
    )
    
    await update.message.reply_text(text, reply_markup=PremiumUI.payment_methods(), parse_mode="Markdown")
    return CHOOSING_METHOD

async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.split("_")[2]
    context.user_data['deposit_method'] = method
    
    if method == "Amazon":
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
            "⚠️ *Note: We only accept INR Gift Cards.*\n\n"
            "📸 **Upload the screenshot of your purchased gift card and code below to continue.**"
        )
        keyboard = InlineKeyboardMarkup([PremiumUI.home_button()])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return UPLOADING_SCREENSHOT

    elif method == "Crypto":
        text = (
            "❖ **𝗦𝗲𝗹𝗲𝗰𝘁 𝗖𝗿𝘆𝗽𝘁𝗼𝗰𝘂𝗿𝗿𝗲𝗻𝗰𝘆**\n"
            "──────────────────────\n"
            "Choose your preferred coin for the transfer:"
        )
        await query.edit_message_text(text, reply_markup=PremiumUI.crypto_selection(), parse_mode="Markdown")
        return CHOOSING_CRYPTO

async def choose_crypto_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split("_")[1]
    context.user_data['deposit_crypto_coin'] = coin
    
    addresses = {
        "USDT": settings.usdt_address,
        "BTC": settings.btc_address,
        "ETH": settings.eth_address,
        "SOL": settings.sol_address
    }
    address = addresses.get(coin, "Address not configured.")
    
    text = (
        f"❖ **{coin} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n"
        f"──────────────────────\n"
        f"📤 Send exactly `{context.user_data['deposit_amount']}` {context.user_data['deposit_currency']} worth of {coin} to the address below:\n\n"
        f"💳 **Network/Address:**\n`{address}`\n*(Tap to copy)*\n\n"
        f"📸 **Upload your payment screenshot once the transfer is complete.**"
    )
            
    keyboard = InlineKeyboardMarkup([PremiumUI.home_button()])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    return UPLOADING_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ **Format not supported.** Please upload a photo/screenshot.")
        return UPLOADING_SCREENSHOT

    # ... (Keep your database and admin forwarding logic exactly the same here) ...
    
    text = (
        "✅ **𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗣𝗿𝗼𝗼𝗳 𝗦𝘂𝗯𝗺𝗶𝘁𝘁𝗲𝗱**\n"
        "──────────────────────\n"
        "Your screenshot has been securely forwarded to our verification team.\n\n"
        "⏱️ *Your balance will be updated automatically upon approval.*"
    )
    await update.message.reply_text(text, reply_markup=PremiumUI.main_menu(), parse_mode="Markdown")
    context.user_data.clear()
    return END
    
