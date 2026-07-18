import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.database.core import AsyncSessionLocal
from src.database.models import User, Setting
from sqlalchemy import select
from src.utils.keyboards import PremiumUI
from src.config import settings

logger = logging.getLogger(__name__)

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()
            
            balance_inr = db_user.balance_inr if db_user and db_user.balance_inr else 0.0
            balance_usd = db_user.balance_usd if db_user and db_user.balance_usd else 0.0
            ref_count = db_user.referral_count if db_user and db_user.referral_count else 0
            ref_earnings = db_user.referral_earnings if db_user and db_user.referral_earnings else 0.0
            total_purchases = db_user.total_purchases if db_user and db_user.total_purchases else 0
            join_date = db_user.created_at.strftime('%Y-%m-%d') if db_user and db_user.created_at else "Unknown"
            slots_left = max(0, 50 - ref_count)
            
            bot_username = context.bot.username
            ref_link = f"https://t.me/{bot_username}?start={user.id}"

            text = (
                "❖ **𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲 & 𝗪𝗮𝗹𝗹𝗲𝘁**\n"
                "──────────────────────\n"
                f"👤 **Name:** {user.first_name}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📅 **Joined:** {join_date}\n\n"
                f"💰 **Wallet Balance:** ₹{balance_inr} | ${balance_usd}\n"
                f"📦 **Total Purchases:** {total_purchases}\n\n"
                f"🎁 **Referral Stats**\n"
                f"• Count: {ref_count}/50\n"
                f"• Earnings: ₹{ref_earnings}\n"
                f"• Slots Left: {slots_left}\n\n"
                f"🔗 **Your Link:**\n`{ref_link}`"
            )
            await update.message.reply_text(text, reply_markup=PremiumUI.deposit_to_wallet(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Profile Error: {e}")
        await update.message.reply_text("An error occurred loading your profile. Please try again.")

async def handle_main_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Setting).where(Setting.key == "MAIN_CHANNEL_LINK"))
        setting = result.scalar_one_or_none()
        channel_link = setting.value if setting else "https://t.me/telegram"
        
    text = "📢 Click the button below to join our official updates channel."
    await update.message.reply_text(text, reply_markup=PremiumUI.link_button("Join Channel", channel_link))

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_url = f"https://t.me/{settings.owner_username.replace('@', '')}"
    text = "💬 Click the button below to contact the Admin directly."
    await update.message.reply_text(text, reply_markup=PremiumUI.link_button("Message Admin", admin_url))
    
