from telegram import Update
from telegram.ext import ContextTypes
from src.database.core import AsyncSessionLocal
from src.database.models import User, Setting
from sqlalchemy import select
from src.utils.keyboards import PremiumUI
from src.config import settings

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # (Keep your existing handle_profile code here exactly as it is)
    pass 

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
    
