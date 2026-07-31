import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.error import Forbidden, BadRequest
from telegram.ext import ContextTypes, ConversationHandler
from src.database.core import AsyncSessionLocal
from src.database.models import User
from sqlalchemy import select, func
from src.config import settings
from src.utils.keyboards import PremiumUI
from src.utils.states import BROADCAST_WAITING, BROADCAST_CONFIRM, END

logger = logging.getLogger(__name__)

async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return
        
    try:
        async with AsyncSessionLocal() as session:
            total_stmt = select(func.count(User.id))
            total_users_count = await session.scalar(total_stmt)
            
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            active_stmt = select(func.count(User.id)).where(User.last_active >= seven_days_ago)
            active_users_count = await session.scalar(active_stmt) or 0
            
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_stmt = select(func.count(User.id)).where(User.created_at >= today_start)
            today_users_count = await session.scalar(today_stmt) or 0

        text = (
            "📊 **Bot Statistics**\n\n"
            f"👥 **Total Registered Users:** {total_users_count:,}\n\n"
            f"🟢 **Active Users (Last 7 Days):** {active_users_count:,}\n\n"
            f"📅 **Today's New Users:** {today_users_count:,}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Total Users Error: {e}")
        await update.message.reply_text("❌ Failed to fetch statistics.")

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return ConversationHandler.END
        
    await update.message.reply_text(
        "📢 **Send the message, photo, video, document, or other content that you want to broadcast to all registered users.**", 
        parse_mode="Markdown"
    )
    return BROADCAST_WAITING

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message
    await update.message.reply_text(
        "📢 **Are you sure you want to broadcast this message?**", 
        reply_markup=PremiumUI.broadcast_confirm(),
        parse_mode="Markdown"
    )
    return BROADCAST_CONFIRM

async def _broadcast_background_task(bot, msg, all_users, status_message):
    total = len(all_users)
    delivered = 0
    failed = 0
    blocked = 0
    deleted = 0
    
    start_time = datetime.now(timezone.utc)
    
    for idx, user_id in enumerate(all_users, 1):
        try:
            await msg.copy(chat_id=user_id)
            delivered += 1
        except Forbidden:
            blocked += 1
        except BadRequest as e:
            if "not found" in str(e).lower() or "deactivated" in str(e).lower():
                deleted += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast Exception for {user_id}: {e}")
            
        if idx % 500 == 0:
            try:
                await status_message.edit_text(f"📢 Broadcasting...\n\n📤 Sent: {idx} / {total}", parse_mode="Markdown")
            except Exception:
                pass
                
        await asyncio.sleep(0.05) # Rate limit protection
                
    time_taken = (datetime.now(timezone.utc) - start_time).seconds
    
    report = (
        "📊 **Broadcast Report**\n\n"
        f"👥 **Total Users:** {total:,}\n"
        f"✅ **Delivered:** {delivered:,}\n"
        f"❌ **Failed:** {failed:,}\n"
        f"🚫 **Blocked:** {blocked:,}\n"
        f"🗑 **Deleted Accounts:** {deleted:,}\n\n"
        f"⏱ **Time Taken:** {time_taken} Seconds"
    )
    try:
        await status_message.edit_text(report, parse_mode="Markdown")
    except Exception:
        await bot.send_message(chat_id=status_message.chat_id, text=report, parse_mode="Markdown")

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "bc_cancel":
        await query.edit_message_text("❌ **Broadcast Cancelled.**", parse_mode="Markdown")
        context.user_data.pop('broadcast_msg', None)
        return ConversationHandler.END
        
    status_msg = await query.edit_message_text("🔄 **Broadcast starting...**", parse_mode="Markdown")
    msg = context.user_data.get('broadcast_msg')
    
    if not msg:
        await query.message.reply_text("❌ Error: Message data lost.")
        return ConversationHandler.END
        
    async with AsyncSessionLocal() as session:
        users_stmt = select(User.telegram_id)
        result = await session.execute(users_stmt)
        all_users = result.scalars().all()
        
    # Start the broadcast securely in the background
    asyncio.create_task(_broadcast_background_task(context.bot, msg, all_users, status_msg))
    
    context.user_data.pop('broadcast_msg', None)
    return ConversationHandler.END

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id: return
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        async with AsyncSessionLocal() as session:
            db_user = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = db_user.scalar_one_or_none()
            if db_user:
                db_user.balance_inr += amount
                await session.commit()
                await update.message.reply_text(f"✅ Added {amount} INR to {user_id}.")
                await context.bot.send_message(chat_id=user_id, text=f"💰 Admin added {amount} INR to your wallet.")
    except Exception:
        await update.message.reply_text("Usage: /addbalance <user_id> <amount>")

async def remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id: return
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        async with AsyncSessionLocal() as session:
            db_user = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = db_user.scalar_one_or_none()
            if db_user:
                db_user.balance_inr = max(0, db_user.balance_inr - amount)
                await session.commit()
                await update.message.reply_text(f"✅ Removed {amount} INR from {user_id}.")
    except Exception:
        await update.message.reply_text("Usage: /removebalance <user_id> <amount>")
        
