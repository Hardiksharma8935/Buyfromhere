import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from src.database.core import AsyncSessionLocal
from src.database.models import User
from src.utils.states import *
from src.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)

# --- BROADCAST SYSTEM ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return
    await update.message.reply_text("📢 **Broadcast Mode**\n\nSend the message you want to broadcast (Text, Photo, Video, File, etc.).\n\nSend /cancel to abort.", parse_mode="Markdown")
    return BROADCAST_WAITING

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Broadcasting started... Please wait.")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.telegram_id))
        users = result.scalars().all()
        
    total = len(users)
    delivered = 0
    failed = 0
    blocked = 0
    deleted = 0
    
    for uid in users:
        try:
            # copy_message flawlessly handles all formatting, spoilers, media, and captions natively
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
            delivered += 1
        except Forbidden:
            blocked += 1
        except BadRequest as e:
            if "chat not found" in str(e).lower() or "deleted" in str(e).lower():
                deleted += 1
            else:
                failed += 1
        except Exception:
            failed += 1
            
    stats = (f"📢 **Broadcast Complete**\n\n"
             f"👥 **Total Users:** {total}\n"
             f"✅ **Delivered:** {delivered}\n"
             f"❌ **Failed:** {failed}\n"
             f"🚫 **Blocked:** {blocked}\n"
             f"🗑️ **Deleted Accounts:** {deleted}")
             
    await update.message.reply_text(stats, parse_mode="Markdown")
    return END

# --- WALLET COMMANDS ---
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: `/addbalance <user_id> <amount>`", parse_mode="Markdown")
        return
        
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        
        async with AsyncSessionLocal() as session:
            user = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = user.scalar_one_or_none()
            if not db_user:
                await update.message.reply_text("❌ User not found in database.")
                return
                
            db_user.balance_inr += amount
            await session.commit()
            
        await update.message.reply_text(f"✅ Successfully added ₹{amount} to {user_id}'s wallet.")
        try:
            await context.bot.send_message(chat_id=user_id, text=f"💰 **Balance Update**\n\n₹{amount} has been added to your wallet by the Admin.", parse_mode="Markdown")
        except Exception:
            pass
            
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID or Amount.")

async def remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.owner_id:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: `/removebalance <user_id> <amount>`", parse_mode="Markdown")
        return
        
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        
        async with AsyncSessionLocal() as session:
            user = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = user.scalar_one_or_none()
            if not db_user:
                await update.message.reply_text("❌ User not found in database.")
                return
                
            db_user.balance_inr = max(0.0, db_user.balance_inr - amount)
            await session.commit()
            
        await update.message.reply_text(f"✅ Successfully removed ₹{amount} from {user_id}'s wallet.")
        try:
            await context.bot.send_message(chat_id=user_id, text=f"💰 **Balance Update**\n\n₹{amount} has been deducted from your wallet by the Admin.", parse_mode="Markdown")
        except Exception:
            pass
            
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID or Amount.")
