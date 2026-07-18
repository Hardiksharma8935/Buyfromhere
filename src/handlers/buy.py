from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from src.utils.states import *
from src.config import settings
from src.database.models import Group, DemoGroup, User
from src.database.core import AsyncSessionLocal
from sqlalchemy import select
from src.utils.keyboards import PremiumUI

# --- DEMO FLOW ---
async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DemoGroup).where(DemoGroup.is_active == True))
        groups = result.scalars().all()
        
    if not groups:
        await update.message.reply_text("❌ No demo groups available at the moment.")
        return
        
    keyboard = [[InlineKeyboardButton(f"🎬 {g.name} Demo", url=g.demo_link)] for g in groups]
    await update.message.reply_text("❖ **𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗗𝗲𝗺𝗼𝘀**\n──────────────────────\nSelect a group to view its demo:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- BUY FLOW ---
async def start_buy_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Group).where(Group.is_active == True))
        groups = result.scalars().all()
        
    if not groups:
        await update.message.reply_text("❌ No groups available for purchase at the moment.")
        return END

    keyboard = [[InlineKeyboardButton(f"{g.name} - ₹{g.price_inr} | ${g.price_usd}", callback_data=f"buy_sel_{g.id}")] for g in groups]
    keyboard.append(PremiumUI.cancel_inline())
    await update.message.reply_text("❖ **𝗕𝘂𝘆 𝗚𝗿𝗼𝘂𝗽𝘀**\n──────────────────────\nSelect a group to purchase:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return BUY_CHOOSING_CURRENCY

async def buy_choose_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split("_")[2])
    context.user_data['buy_group_id'] = group_id
    
    async with AsyncSessionLocal() as session:
        group = await session.get(Group, group_id)
        
    text = (f"❖ **{group.name}**\n──────────────────────\n📝 {group.description or 'No description'}\n\n"
            f"🇮🇳 **INR Price:** ₹{group.price_inr}\n🇺🇸 **USD Price:** ${group.price_usd}\n\nSelect your payment currency:")
    await query.edit_message_text(text, reply_markup=PremiumUI.buy_currency_selection(group_id), parse_mode="Markdown")
    return BUY_CHOOSING_METHOD

async def buy_choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    currency = query.data.split("_")[2]
    group_id = int(query.data.split("_")[3])
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
    
    async with AsyncSessionLocal() as session:
        group = await session.get(Group, group_id)
        amount = group.price_inr if currency == "INR" else group.price_usd
    context.user_data['buy_amount'] = amount

    if method == "Amazon":
        text = f"❖ **𝗔𝗺𝗮𝘇𝗼𝗻 𝗚𝗶𝗳𝘁 𝗖𝗮𝗿𝗱**\n──────────────────────\n🛒 **Required:** {amount} {currency} Gift Card\n\n⌨️ **Please type and send your Gift Card Code below.**"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_GC_CODE
    else:
        text = f"❖ **{method} 𝗣𝗮𝘆𝗺𝗲𝗻𝘁**\n──────────────────────\n📤 Send exactly `{amount}` {currency}.\n\nClick the button below once you have paid."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I Paid", callback_data="buy_i_paid")], PremiumUI.cancel_inline()]), parse_mode="Markdown")
        return BUY_SCREENSHOT

async def buy_receive_gc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user = update.message.from_user
    group_id = context.user_data['buy_group_id']
    
    admin_text = (f"🚨 **New Group Purchase (Amazon GC)**\n\n👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n"
                  f"📦 Group ID: {group_id}\n💵 Amount: {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"🎟️ Code: `{code}`\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    await context.bot.send_message(chat_id=settings.owner_id, text=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ Code submitted. Please wait for admin verification.")
    context.user_data.clear()
    return END

async def buy_request_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📸 **Upload your payment screenshot below to continue.**", reply_markup=InlineKeyboardMarkup([PremiumUI.cancel_inline()]), parse_mode="Markdown")
    return BUY_SCREENSHOT

async def buy_receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a photo/screenshot.")
        return BUY_SCREENSHOT

    photo_file_id = update.message.photo[-1].file_id
    user = update.message.from_user
    group_id = context.user_data['buy_group_id']
    
    admin_text = (f"🚨 **New Group Purchase (Screenshot)**\n\n👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n"
                  f"📦 Group ID: {group_id}\n💵 Amount: {context.user_data['buy_amount']} {context.user_data['buy_currency']}\n"
                  f"💳 Method: {context.user_data['buy_method']}\n🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"buy_app_{group_id}_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"buy_rej_{user.id}")]]
    await context.bot.send_photo(chat_id=settings.owner_id, photo=photo_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ Proof submitted. Please wait for admin verification.")
    context.user_data.clear()
    return END

# --- ADMIN AUTO-DELIVERY LOGIC ---
async def admin_buy_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split("_")[1]
    
    if action == "app":
        group_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        
        async with AsyncSessionLocal() as session:
            group = await session.get(Group, group_id)
            user = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = user.scalar_one_or_none()
            if db_user:
                db_user.total_purchases += 1
                await session.commit()
                
        # Generate or Fetch Invite Link
        final_link = group.invite_link
        if group.telegram_group_id:
            try:
                invite = await context.bot.create_chat_invite_link(chat_id=group.telegram_group_id, member_limit=1)
                final_link = invite.invite_link
            except Exception:
                pass # Fallback to DB link if bot is not admin in the channel

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ **Purchase Approved!**\n\nHere is your unique access link for **{group.name}**:\n{final_link}\n\n*Note: This link is single-use.*",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        if query.message.photo:
            await query.edit_message_caption(caption=query.message.caption + "\n\n**STATUS: APPROVED & LINK SENT ✅**")
        else:
            await query.edit_message_text(text=query.message.text + "\n\n**STATUS: APPROVED & LINK SENT ✅**")
            
    elif action == "rej":
        user_id = int(query.data.split("_")[2])
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ **Purchase Rejected.**\nYour payment could not be verified.", parse_mode="Markdown")
        except Exception:
            pass
        if query.message.photo:
            await query.edit_message_caption(caption=query.message.caption + "\n\n**STATUS: REJECTED ❌**")
        else:
            await query.edit_message_text(text=query.message.text + "\n\n**STATUS: REJECTED ❌**")
            
