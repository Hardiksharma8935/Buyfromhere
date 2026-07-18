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

# [DEMO AND BUY START FUNCTIONS REMAIN UNCHANGED - KEEP YOUR CURRENT ONES]

async def admin_buy_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Callback data: buy_app_{group_id}_{user_id}
    data_parts = query.data.split("_")
    action = data_parts[1]
    
    try:
        if action == "app":
            group_id = data_parts[2]
            user_id = int(data_parts[3])
            group = GROUPS[group_id]
            
            # 1. Update DB
            async with AsyncSessionLocal() as session:
                user = await session.execute(select(User).where(User.telegram_id == user_id))
                db_user = user.scalar_one_or_none()
                if db_user:
                    db_user.total_purchases += 1
                    await session.commit()
            
            # 2. Try Generating Link
            try:
                invite = await context.bot.create_chat_invite_link(chat_id=group["chat_id"], member_limit=1)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **Purchase Approved!**\nAccess link for **{group['name']}**:\n{invite.invite_link}\n\n⚠️ *One-time use only.*",
                    parse_mode="Markdown"
                )
                await query.edit_message_text(f"{query.message.text}\n\n✅ APPROVED & LINK SENT")
            except Exception as e:
                logger.error(f"Invite Link Error: {e}")
                await context.bot.send_message(settings.owner_id, f"❌ Failed to generate link for user {user_id}. Error: {e}")
                await query.edit_message_text(f"{query.message.text}\n\n❌ FAILED TO GEN LINK (Check Bot Permissions)")

        elif action == "rej":
            user_id = int(data_parts[2])
            await context.bot.send_message(chat_id=user_id, text="❌ **Purchase Rejected.** Contact Admin.")
            await query.edit_message_text(f"{query.message.text}\n\n❌ REJECTED")
            
    except Exception as e:
        logger.error(f"Admin Action Crash: {e}")
        
