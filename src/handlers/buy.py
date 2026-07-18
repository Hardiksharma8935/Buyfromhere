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
    await update.message.reply_text("❖ **𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗗𝗲𝗺𝗼𝘀**\n──────────────────────\nSelect a group to view its demo:", reply_markup=PremiumUI.demo_list(), parse_mode="Markdown")

async def start_buy_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GROUPS:
        await update.message.reply_text("❌ No groups available for purchase.")
        return END
    await update.message.reply_text("❖ **𝗕𝘂𝘆 𝗚𝗿𝗼𝘂𝗽𝘀**\n──────────────────────\nSelect a group to purchase:", reply_markup=PremiumUI.group_list(), parse_mode="Markdown")
    return BUY_CHOOSING_CURRENCY

async def buy_choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = query.data.split("_")[2]
    context.user_data['buy_group_id'] = group_id
    group = GROUPS[group_id]
        
    text = (f"❖ **{group['name']}**\n──────────────────────\n📝 {group.get('description', 'No description')}\n\n"
            f"🇮🇳 **INR Price:** ₹{group['price']}\n🇺🇸 **USD Price:** ${group['usd_price']}\n⭐ **Stars Price:** {group['stars']}\n\nSelect your payment currency:")
    await query.edit_message_text(text, reply_markup=PremiumUI.buy_currency_selection(group_id), parse_mode="Markdown")
    return BUY_CHOOSING_METHOD

async def buy_choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    currency = query.data.split("_")[2]
    group_id = query.data.split("_")[3]
    context.user_data['buy_currency'] = currency
    await query.edit_message_text("❖ **𝗦𝗲𝗹𝗲𝗰𝘁 𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗠𝗲𝘁𝗵𝗼𝗱**\n──────────────────────\nHow would you like to pay?", reply_markup=PremiumUI.buy_payment_methods(group_id), parse_mode="Markdown")
    return BUY_GC_CODE

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

    if method == "Stars":
        await query.message.delete()
        title = group['name']
        description = f"Purchase access to {group['name']}"
        payload = f"buy_{group_id}_{update.effective_user.id}"
        currency = "XTR"
        price = group['stars']
        prices = [LabeledPrice("Group Access", price)]
        
        await context.bot.send_invoice(
            chat_id=update.effective_user.id,
            title=title, description=description, payload=payload,
            provider_token="", currency=currency, prices=prices
        )
        return END

    elif method == "Amazon":
        text = f"❖ **𝗔𝗺𝗮𝘇𝗼𝗻 𝗚𝗶𝗳𝘁 𝗖𝗮𝗿𝗱**\n──────────────────────\n🛒 **Required:** {amount} {currency} Gift Card\n\n⌨️ **Please type and send your Gift Card Code below.**"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_GC_CODE
    else:
        text = f"❖ **{method} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n──────────────────────\n📤 Send exactly `{amount}` {currency}.\n\nClick the button below once you have paid."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I Paid", callback_data="buy_i_paid")], PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_SCREENSHOT

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

        # Generate Invite Link
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
            
async def buy_receive_gc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user = update.message.from_user
    group_id = context.user_data['buy_group_id']
    
    admin_text = (f"🚨 **New Group Purchase (Amazon GC)**\n\n👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n"
                  f"📦 Group Name: {GROUPS[group_id]['name']}\n💵 Amount: {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"🎟️ Code: `{code}`\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    await context.bot.send_message(chat_id=settings.owner_id, text=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ Code submitted. Please wait for admin verification.", reply_markup=PremiumUI.main_menu())
    context.user_data.clear()
    return END

async def buy_request_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📸 **Upload your payment screenshot below to continue.**", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
    return BUY_SCREENSHOT

async def buy_receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a valid photo/screenshot.")
        return BUY_SCREENSHOT

    photo_file_id = update.message.photo[-1].file_id
    user = update.message.from_user
    group_id = context.user_data['buy_group_id']
    
    admin_text = (f"🚨 **New Group Purchase (Screenshot)**\n\n👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n"
                  f"📦 Group Name: {GROUPS[group_id]['name']}\n💵 Amount: {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"💳 Method: {context.user_data['buy_method']}\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    await context.bot.send_photo(chat_id=settings.owner_id, photo=photo_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ Proof submitted. Please wait for admin verification.", reply_markup=PremiumUI.main_menu())
    context.user_data.clear()
    return END

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
    
