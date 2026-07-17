from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.utils.states import *
from src.config import settings
from src.database.models import Transaction
from src.database.core import AsyncSessionLocal

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("INR (₹)", callback_data="dep_curr_INR"),
         InlineKeyboardButton("USD ($)", callback_data="dep_curr_USD")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    await update.callback_query.edit_message_text(
        "Please select the currency for your deposit:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_CURRENCY

async def choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    currency = query.data.split("_")[2]
    context.user_data['deposit_currency'] = currency
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="cancel_deposit")]]
    await query.edit_message_text(
        f"You selected {currency}.\n\nPlease enter the amount you wish to deposit (e.g., 500):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TYPING_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a valid number or /cancel.")
        return TYPING_AMOUNT

    context.user_data['deposit_amount'] = amount
    
    keyboard = [
        [InlineKeyboardButton("Amazon Gift Card", callback_data="dep_meth_Amazon")],
        [InlineKeyboardButton("Crypto (USDT, BTC, ETH, SOL)", callback_data="dep_meth_Crypto")],
        [InlineKeyboardButton("Telegram Stars", callback_data="dep_meth_Stars")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_deposit")]
    ]
    
    await update.message.reply_text(
        f"Amount: {amount} {context.user_data['deposit_currency']}\n\nChoose a payment method:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_METHOD

async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.split("_")[2]
    context.user_data['deposit_method'] = method
    
    if method == "Amazon":
        currency = context.user_data['deposit_currency']
        amount = context.user_data['deposit_amount']
        
        # Enforce INR for Amazon Gift Cards
        if currency == "USD":
            amount = amount * settings.usd_to_inr_rate
            context.user_data['deposit_amount'] = amount
            context.user_data['deposit_currency'] = "INR"
            
        text = (f"🛍 **Amazon Gift Card (India Only)**\n\n"
                f"Please send a **₹{amount}** Amazon Gift Card.\n"
                f"*Note: We only accept INR Gift Cards.*\n\n"
                f"Upload the screenshot of your purchased gift card and code below.")
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="cancel_deposit")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return UPLOADING_SCREENSHOT

    elif method == "Crypto":
        keyboard = [
            [InlineKeyboardButton("USDT (BEP20/TRC20)", callback_data="crypto_USDT"),
             InlineKeyboardButton("BTC", callback_data="crypto_BTC")],
            [InlineKeyboardButton("ETH", callback_data="crypto_ETH"),
             InlineKeyboardButton("SOL", callback_data="crypto_SOL")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_deposit")]
        ]
        await query.edit_message_text("Select a Cryptocurrency:", reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    text = (f"🪙 **{coin} Payment**\n\n"
            f"Send exactly `{context.user_data['deposit_amount']}` {context.user_data['deposit_currency']} worth of {coin} to:\n\n"
            f"`{address}`\n\n"
            f"(Click address to copy)\n\n"
            f"Once sent, please upload the payment screenshot.")
            
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="cancel_deposit")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return UPLOADING_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo/screenshot.")
        return UPLOADING_SCREENSHOT

    photo_file_id = update.message.photo[-1].file_id
    user = update.message.from_user
    amount = context.user_data['deposit_amount']
    currency = context.user_data['deposit_currency']
    method = context.user_data['deposit_method']
    coin = context.user_data.get('deposit_crypto_coin', '')

    # Save to Database
    async with AsyncSessionLocal() as session:
        new_tx = Transaction(
            user_id=user.id,
            amount=amount,
            currency=currency,
            method=method,
            crypto_coin=coin,
            screenshot_id=photo_file_id,
            status="Pending"
        )
        session.add(new_tx)
        await session.commit()
        await session.refresh(new_tx)
        tx_id = new_tx.id

    # Send to Admin
    admin_text = (f"🚨 **New Deposit Request**\n\n"
                  f"👤 User: {user.first_name} (@{user.username})\n"
                  f"🆔 ID: `{user.id}`\n"
                  f"💵 Amount: {amount} {currency}\n"
                  f"💳 Method: {method} {coin}\n"
                  f"🕒 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
                  
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{tx_id}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{tx_id}")]
    ]
    
    await context.bot.send_photo(
        chat_id=settings.owner_id,
        photo=photo_file_id,
        caption=admin_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ **Payment proof sent successfully.**\nWaiting for Admin verification.", parse_mode="Markdown")
    context.user_data.clear()
    return END

async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.edit_message_text("Deposit cancelled.")
    else:
        await update.message.reply_text("Deposit cancelled.")
    return END
          
