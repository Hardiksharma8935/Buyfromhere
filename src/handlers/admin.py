from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from src.database.core import AsyncSessionLocal
from src.database.models import Group, DemoGroup, Setting
from src.utils.keyboards import PremiumUI
from src.utils.states import *
from src.config import settings

async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return
    await update.message.reply_text("👑 **Admin Panel**\nSelect an option to manage your bot:", reply_markup=PremiumUI.admin_main_menu())
    return ADMIN_MENU

async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "admin_home":
        await query.edit_message_text("👑 **Admin Panel**\nSelect an option to manage your bot:", reply_markup=PremiumUI.admin_main_menu())
        return ADMIN_MENU
        
    elif data == "admin_settings":
        await query.edit_message_text("⚙️ **Settings**\nSelect a configuration to update:", reply_markup=PremiumUI.admin_settings_menu())
        return ADMIN_MENU
        
    elif data.startswith("admin_set_"):
        key = data.replace("admin_set_", "")
        context.user_data['setting_key'] = key
        await query.edit_message_text(f"Please send the new value for **{key}**:\n\nSend /cancel to abort.", parse_mode="Markdown")
        return ADMIN_SET_SETTING

    elif data == "admin_groups":
        keyboard = [[InlineKeyboardButton("➕ Add New Group", callback_data="admin_add_group")], [InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]
        await query.edit_message_text("📦 **Group Management**\nAdd or remove premium groups.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADMIN_MENU
        
    elif data == "admin_add_group":
        await query.edit_message_text("Send the **Name** of the new group (e.g. Premium Movies):")
        return ADMIN_G_NAME

    elif data == "admin_demos":
        keyboard = [[InlineKeyboardButton("➕ Add New Demo", callback_data="admin_add_demo")], [InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]
        await query.edit_message_text("🎬 **Demo Management**\nAdd or remove demo links.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADMIN_MENU
        
    elif data == "admin_add_demo":
        await query.edit_message_text("Send the **Name** of the Demo Group:")
        return ADMIN_D_NAME

async def admin_receive_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.get('setting_key')
    value = update.message.text
    async with AsyncSessionLocal() as session:
        setting = await session.get(Setting, key)
        if setting:
            setting.value = value
        else:
            session.add(Setting(key=key, value=value))
        await session.commit()
    await update.message.reply_text(f"✅ Setting `{key}` updated to:\n{value}", parse_mode="Markdown")
    return END

async def admin_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['g_name'] = update.message.text
    await update.message.reply_text("Send the **Description**:")
    return ADMIN_G_DESC

async def admin_g_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['g_desc'] = update.message.text
    await update.message.reply_text("Send the **INR Price** (Number only):")
    return ADMIN_G_INR

async def admin_g_inr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['g_inr'] = float(update.message.text)
    await update.message.reply_text("Send the **USD Price** (Number only):")
    return ADMIN_G_USD

async def admin_g_usd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['g_usd'] = float(update.message.text)
    await update.message.reply_text("Send the **Telegram Group ID** (e.g., -100123456789) or type '0' to skip:")
    return ADMIN_G_ID

async def admin_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    context.user_data['g_id'] = int(val) if val != '0' else None
    await update.message.reply_text("Send the fallback **Invite Link** (https://t.me/...):")
    return ADMIN_G_LINK

async def admin_g_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        session.add(Group(
            name=context.user_data['g_name'], description=context.user_data['g_desc'],
            price_inr=context.user_data['g_inr'], price_usd=context.user_data['g_usd'],
            telegram_group_id=context.user_data['g_id'], invite_link=update.message.text,
            purchase_link="", demo_link="" # Overriding NOT NULL constraints from old DB
        ))
        await session.commit()
    await update.message.reply_text("✅ Group added successfully!")
    context.user_data.clear()
    return END

async def admin_d_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_name'] = update.message.text
    await update.message.reply_text("Send the **Demo Link** (https://t.me/...):")
    return ADMIN_D_LINK

async def admin_d_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        session.add(DemoGroup(name=context.user_data['d_name'], demo_link=update.message.text))
        await session.commit()
    await update.message.reply_text("✅ Demo added successfully!")
    context.user_data.clear()
    return END
    
