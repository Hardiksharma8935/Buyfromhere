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

# --- DEMO LOGIC ---
async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 **Demo Groups**\nSelect a group to view:", reply_markup=PremiumUI.demo_list(), parse_mode="Markdown")

async def demo_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Instant UI response
    
    group_id = query.data.split("_")[2]
    group = GROUPS.get(group_id)
    
    if not group:
        await query.edit_message_text("❌ Demo not found.")
        return
        
    text = f"❖ **{group['name']}**\n──────────────────────\n📝 {group.get('description', 'No description available.')}\n\nClick below to open the demo."
    await query.edit_message_text(text, reply_markup=PremiumUI.link_button("🔗 Open Demo", group['demo']), parse_mode="Markdown")

# --- BUY LOGIC ---
async def start_buy_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GROUPS:
        await update.message.reply_text("❌ No groups available for purchase.")
        return END
    await update.message.reply_text("🛒 **Buy Groups**\nSelect a group to purchase:", reply_markup=PremiumUI.group_list(), parse_mode="Markdown")
    return BUY_CHOOSING_CURRENCY

async def buy_choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = query.data.split("_")[2]
    context.user_data['buy_group_id'] = group_id
    group = GROUPS[group_id]
    
    text = f"❖ **{group['name']}**\n\n🇮🇳 ₹{group['price']} | 🇺🇸 ${group['usd_price']} | ⭐ {group['stars']}\n\nChoose currency:"
    await query.edit_message_text(text, reply_markup=PremiumUI.buy_currency_selection(group_id), parse_mode="Markdown")
    return BUY_CHOOSING_METHOD

async def buy_choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    currency = query.data.split("_")[2]
    group_id = query.data.split("_")[3]
    context.user_data['buy_currency'] = currency
    context.user_data['buy_group_id'] = group_id
    
    await query.edit_message_text("💳 Select Payment Method:", reply_markup=PremiumUI.buy_payment_methods(group_id), parse_mode="Markdown")
    return BUY_CHOOSING_CRYPTO # Routing hub

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
        text = f"❖ **𝗔𝗺𝗮𝘇𝗼𝗻 𝗚𝗶𝗳𝘁 𝗖𝗮𝗿𝗱**\n──────────────────────\n🛒 **Required:** {amount} {currency} Gift Card\n\nPlease purchase the gift card and click 'I Paid'."
        await query.edit_message_text(text, reply_markup=PremiumUI.i_paid_keyboard("buy"), parse_mode="Markdown")
        return BUY_CONFIRM_PAYMENT

async def buy_crypto_coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split("_")[2] # buy_crypt_USDT
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
        await query.edit_message_text("📸 Please type and send your Gift Card Code below:", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_GC_CODE
    else:
        await query.edit_message_text("📸 Please upload your payment screenshot below:", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_SCREENSHOT

async def buy_receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = context.user_data['buy_group_id']
    group = GROUPS[group_id]
    
    proof = update.message.text or "Screenshot provided"
    
    admin_text = (f"🚨 **New Purchase Request**\n\n👤 {user.full_name} (@{user.username})\n🆔 `{user.id}`\n"
                  f"📦 {group['name']}\n💵 {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"💳 Method: {context.user_data.get('buy_method', 'Unknown')} {context.user_data.get('buy_crypto_coin', '')}\n"
                  f"🎟️ Proof: {proof}")
    
    btn = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    
    if update.message.photo:
        await context.bot.send_photo(settings.owner_id, update.message.photo[-1].file_id, caption=admin_text, reply_markup=InlineKeyboardMarkup(btn))
    else:
        await context.bot.send_message(settings.owner_id, admin_text, reply_markup=InlineKeyboardMarkup(btn))
        
    await update.message.reply_text("✅ Proof sent to admin. Verification in progress.", reply_markup=PremiumUI.main_menu())
    context.user_data.clear()
    return END

# --- TELEGRAM STARS PAYMENT HANDLERS ---
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_"):
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
            if db_user:
                db_user.total_purchases += 1
            
            new_tx = Transaction(user_id=user.id, amount=payment.total_amount, currency=payment.currency, method="Stars", status="Approved")
            session.add(new_tx)
            await session.commit()

        # Generate Invite Link Automatically
        try:
            invite = await context.bot.create_chat_invite_link(chat_id=group["chat_id"], member_limit=1, name=f"Stars_{user.id}")
            final_link = invite.invite_link
            await update.message.reply_text(
                f"✅ **Payment Successful!**\n\nHere is your unique access link for **{group['name']}**:\n{final_link}\n\n⚠️ *Note: This link is strictly single-use and will expire immediately after you join.*",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Stars Invite Link Error: {e}")
            await update.message.reply_text("✅ Payment successful, but we couldn't generate the invite link. Please contact Admin.")

# --- ADMIN ACTION HANDLERS ---
async def admin_buy_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        action = query.data.split("_")[1]
        
        if action == "app":
            group_id = query.data.split("_")[2]
            user_id = int(query.data.split("_")[3])
            group = GROUPS[group_id]
            
            async with AsyncSessionLocal() as session:
                user = await session.execute(select(User).where(User.telegram_id == user_id))
                db_user = user.scalar_one_or_none()
                if db_user:
                    db_user.total_purchases += 1
                    await session.commit()
                    
            try:
                invite = await context.bot.create_chat_invite_link(chat_id=group["chat_id"], member_limit=1, name=f"Purchase_{user_id}")
                final_link = invite.invite_link
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **Purchase Approved!**\n\nHere is your unique access link for **{group['name']}**:\n{final_link}\n\n⚠️ *Note: This link is strictly single-use and will expire immediately after you join.*",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to generate invite link: {e}")
                
            if query.message.photo:
                await query.edit_message_caption(caption=query.message.caption + "\n\n**STATUS: APPROVED & LINK SENT ✅**")
            else:
                await query.edit_message_text(text=query.message.text + "\n\n**STATUS: APPROVED & LINK SENT ✅**")
                
        elif action == "rej":
            user_id = int(query.data.split("_")[2])
            try:
                await context.bot.send_message(chat_id=user_id, text="❌ **Purchase Rejected.**\nYour payment could not be verified. Contact Admin.", parse_mode="Markdown")
            except Exception:
                pass
            if query.message.photo:
                await query.edit_message_caption(caption=query.message.caption + "\n\n**STATUS: REJECTED ❌**")
            else:
                await query.edit_message_text(text=query.message.text + "\n\n**STATUS: REJECTED ❌**")
                
    except Exception as e:
        logger.error(f"Admin Buy Action Error: {e}")
