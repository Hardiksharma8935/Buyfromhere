from telegram import Update
from telegram.ext import ContextTypes
from src.database.core import AsyncSessionLocal
from src.database.models import User
from sqlalchemy import select

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        balance_inr = db_user.balance_inr if db_user else 0.0
        balance_usd = db_user.balance_usd if db_user else 0.0
        
        text = (
            "❖ **𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲**\n"
            "──────────────────────\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n\n"
            f"💰 **Balance:** ₹{balance_inr} | ${balance_usd}\n"
            f"🎁 **Referrals:** {db_user.referral_count if db_user else 0}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

async def handle_coming_soon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature = update.message.text.replace(" ", "")
    text = (
        f"❖ **{feature}**\n"
        "──────────────────────\n"
        "This feature is currently under development and will be available soon."
    )
    await update.message.reply_text(text, parse_mode="Markdown")
  
