import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from src.utils.states import *
from src.config import settings
from src.groups_config import GROUPS
from src.database.models import User, Transaction
from src.database.core import AsyncSessionLocal
from sqlalchemy import select
from src.utils.keyboards import PremiumUI

logger = logging.getLogger(__name__)

async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 **Demo Groups**\nSelect a group to view:", reply_markup=PremiumUI.demo_list(), parse_mode="Markdown")

async def demo_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    group_id = query.data.split("_")[2]
    group = GROUPS.get(group_id)
    if not group: return
    text = f"❖ **{group['name']}**\n──────────────────────\n📝 {group.get('description', 'No description available.')}\n\nClick below to open the demo."
    await query.edit_message_text(text, reply_markup=PremiumUI.link_button("🔗 Open Demo", group['demo']), parse_mode="Markdown")

async def start_buy_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if not GROUPS:
        await update.message.reply_text("❌ No groups available for purchase.")
        return END
    await update.message.reply_text("🛒 **Buy Groups**\nSelect a group to purchase:", reply_markup=PremiumUI.group_list(), parse_mode="Markdown")
    return BUY_CHOOSING_OPTION

async def buy_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = query.data.split("_")[2]
    context.user_data['buy_group_id'] = group_id
    await query.edit_message_text("💳 Choose your purchase method:", reply_markup=PremiumUI.buy_options(group_id), parse_mode="Markdown")
    return BUY_ROUTING

async def buy_option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    opt = query.data.split("_")[2]
    group_id = query.data.split("_")[3]
    group = GROUPS[group_id]
    
    if opt == "wall":
        async with AsyncSessionLocal() as session:
            user = await session.execute(select(User).where(User.telegram_id == update.effective_user.id))
            db_user = user.scalar_one_or_none()
            price_inr = group['price']
            
            if db_user and db_user.balance_inr >= price_inr:
                db_user.balance_inr -= price_inr
                new_tx = Transaction(user_id=update.effective_user.id, amount=price_inr, currency="INR", method="Wallet", status="Approved")
                session.add(new_tx)
                await session.commit()
                
                try:
                    invite = await context.bot.create_chat_invite_link(chat_id=group['chat_id'], member_limit=1, name=f"Wallet_{update.effective_user.id}")
                    await query.edit_message_text(f"✅ **Purchase Successful!**\n\nYour access link for **{group['name']}**:\n{invite.invite_link}\n\n⚠️ *One-time use only.*", parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Invite error: {e}")
                    await query.edit_message_text("✅ Payment deducted, but failed to generate link. Contact Admin.")
            else:
                await query.edit_message_text("❌ **Insufficient wallet balance.**\nPlease deposit funds to continue.", reply_markup=PremiumUI.deposit_to_wallet(), parse_mode="Markdown")
        return END

    else:
        text = f"❖ **{group['name']}**\n\n🇮🇳 ₹{group['price']} | 🇺🇸 ${group['usd_price']} | ⭐ {group['stars']}\n\nChoose currency:"
        await query.edit_message_text(text, reply_markup=PremiumUI.buy_currency_selection(group_id), parse_mode="Markdown")
        return BUY_CHOOSING_CURRENCY

async def buy_choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    currency = query.data.split("_")[2]
    group_id = query.data.split("_")[3]
    context.user_data['buy_currency'] = currency
    
    admin_username = settings.owner_username.replace('@', '')
    await query.edit_message_text("💳 Select Payment Method:", reply_markup=PremiumUI.buy_payment_methods(group_id, admin_username), parse_mode="Markdown")
    return BUY_CHOOSING_METHOD

async def buy_process_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.split("_")[2]
    context.user_data['buy_method'] = method
    group_id = context.user_data['buy_group_id']
    currency = context.user_data['buy_currency']
    
    group = GROUPS[group_id]
    amount = group['price'] if currency == "INR" else group['usd_price']
    context.user_data['buy_amount'] = amount

    if method == "Crypto":
        text = "🪙 **Crypto Payment**\nSelect your coin:"
        await query.edit_message_text(text, reply_markup=PremiumUI.crypto_selection(prefix="buy_crypt"), parse_mode="Markdown")
        return BUY_CHOOSING_CRYPTO 

    elif method == "Stars":
        await query.message.delete()
        title = group['name']
        description = f"Purchase access to {group['name']}"
        payload = f"buy_{group_id}_{update.effective_user.id}"
        prices = [LabeledPrice("Group Access", group['stars'])]
        
        await context.bot.send_invoice(
            chat_id=update.effective_user.id,
            title=title, description=description, payload=payload,
            provider_token="", currency="XTR", prices=prices
        )
        return END

    elif method == "Amazon":
        text = (
            f"❖ **𝗔𝗺𝗮𝘇𝗼𝗻 𝗚𝗶𝗳𝘁 𝗖𝗮𝗿𝗱**\n"
            f"──────────────────────\n"
            f"🛒 **Required:** {amount} {currency} Gift Card\n\n"
            f"⌨️ **Please send your Amazon Gift Card Code (INR) in this chat.**"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_RECEIVING_GC_CODE

async def buy_receive_gc_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gc_code'] = update.message.text
    text = f"✅ **Code Received:** `{update.message.text}`\n\nPlease click **I Paid** to submit this code for verification, or **Cancel** to abort."
    await update.message.reply_text(text, reply_markup=PremiumUI.i_paid_keyboard("buy"), parse_mode="Markdown")
    return BUY_CONFIRM_PAYMENT

async def buy_crypto_coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split("_")[2] 
    context.user_data['buy_crypto_coin'] = coin
    
    addresses = {
        "USDT": settings.usdt_address,
        "BTC": settings.btc_address,
        "ETH": settings.eth_address,
        "SOL": settings.sol_address
    }
    address = addresses.get(coin, "Address not configured.")
    
    text = (f"❖ **{coin} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n──────────────────────\n"
            f"📤 Send exactly `{context.user_data['buy_amount']}` {context.user_data['buy_currency']} to:\n\n"
            f"`{address}`\n\nOnce transferred, click **I Paid**.")
    await query.edit_message_text(text, reply_markup=PremiumUI.i_paid_keyboard("buy"), parse_mode="Markdown")
    return BUY_CONFIRM_PAYMENT

async def buy_ask_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = context.user_data.get('buy_method', '')

    if method == "Amazon":
        user = update.effective_user
        group_id = context.user_data['buy_group_id']
        group = GROUPS[group_id]
        gc_code = context.user_data.get('gc_code', '')
        
        admin_text = (f"🚨 **New Purchase Request (Amazon GC)**\n\n👤 {user.full_name} (@{user.username})\n🆔 `{user.id}`\n"
                      f"📦 {group['name']}\n💵 {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                      f"🎟️ Code: `{gc_code}`\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        btn = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
        await context.bot.send_message(settings.owner_id, admin_text, reply_markup=InlineKeyboardMarkup(btn))
        await query.edit_message_text("✅ Gift Card Code sent to admin. Verification in progress.", parse_mode="Markdown")
        context.user_data.clear()
        return END

    else:
        await query.edit_message_text("📸 Please upload your payment screenshot below:", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_SCREENSHOT

async def buy_receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a valid photo/screenshot.")
        return BUY_SCREENSHOT

    user = update.effective_user
    group_id = context.user_data['buy_group_id']
    group = GROUPS[group_id]
    
    admin_text = (f"🚨 **New Purchase Request (Screenshot)**\n\n👤 {user.full_name} (@{user.username})\n🆔 `{user.id}`\n"
                  f"📦 {group['name']}\n💵 {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"💳 Method: {context.user_data.get('buy_method', 'Unknown')} {context.user_data.get('buy_crypto_coin', '')}\n"
                  f"🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    btn = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    await context.bot.send_photo(settings.owner_id, update.message.photo[-1].file_id, caption=admin_text, reply_markup=InlineKeyboardMarkup(btn))
    await update.message.reply_text("✅ Proof sent to admin. Verification in progress.", reply_markup=PremiumUI.main_menu())
    context.user_data.clear()
    return END

async def admin_buy_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        data_parts = query.data.split("_")
        action = data_parts[1]
        if action == "app":
            group_id = data_parts[2]
            user_id = int(data_parts[3])
            group = GROUPS[group_id]
            
            async with AsyncSessionLocal() as session:
                user = await session.execute(select(User).where(User.telegram_id == user_id))
                db_user = user.scalar_one_or_none()
                if db_user:
                    db_user.total_purchases += 1
                    await session.commit()
            
            try:
                invite = await context.bot.create_chat_invite_link(chat_id=group["chat_id"], member_limit=1, name=f"Purchase_{user_id}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **Purchase Approved!**\nAccess link for **{group['name']}**:\n{invite.invite_link}\n\n⚠️ *Single-use only.*",
                    parse_mode="Markdown"
                )
                await query.edit_message_text(f"{query.message.text}\n\n✅ APPROVED & LINK SENT")
            except Exception as e:
                logger.error(f"Invite Link Error: {e}")
                await context.bot.send_message(settings.owner_id, f"❌ Failed to generate link for user {user_id}. Error: {e}")
                await query.edit_message_text(f"{query.message.text}\n\n❌ FAILED TO GEN LINK")
        elif action == "rej":
            user_id = int(data_parts[2])
            await context.bot.send_message(chat_id=user_id, text="❌ **Purchase Rejected.** Contact Admin.")
            await query.edit_message_text(f"{query.message.text}\n\n❌ REJECTED")
    except Exception as e:
        logger.error(f"Admin Action Crash: {e}")
        
