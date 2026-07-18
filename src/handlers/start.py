import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.core import AsyncSessionLocal
from src.database.models import User
from sqlalchemy import select
from src.utils.keyboards import PremiumUI

async def generate_captcha() -> tuple[str, str]:
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    return f"{num1} + {num2}", str(num1 + num2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            args = context.args
            referred_by = int(args[0]) if args and args[0].isdigit() else None
            
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                referred_by=referred_by
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

        if not db_user.is_verified:
            question, answer = await generate_captcha()
            context.user_data['captcha_answer'] = answer
            
            keyboard = [
                [InlineKeyboardButton(str(random.randint(2, 20)), callback_data="captcha_wrong"),
                 InlineKeyboardButton(answer, callback_data="captcha_correct"),
                 InlineKeyboardButton(str(random.randint(2, 20)), callback_data="captcha_wrong")]
            ]
            random.shuffle(keyboard[0])
            
            await update.message.reply_text(
                f"🛡️ **Security Check**\n\nPlease solve this to verify you are human:\n\n**{question} = ?**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        await show_main_menu(update, context)

async def verify_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "captcha_correct":
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == query.from_user.id)
            result = await session.execute(stmt)
            db_user = result.scalar_one()
            db_user.is_verified = True
            await session.commit()
            
        await query.message.delete()
        await show_main_menu(update, context, is_new=True)
    else:
        await query.edit_message_text("❌ Incorrect. Please use /start to try again.")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False):
    text = (
        "❖ 𝗭𝗲𝗻𝗶𝘁𝗵 𝗡𝗼𝘃𝗮 𝗣𝗮𝘆\n"
        "──────────────────────\n"
        "Welcome to your dashboard. Use the menu below to navigate."
    )
    
    # We must send a new message to attach the ReplyKeyboardMarkup
    if update.message:
        await update.message.reply_text(text, reply_markup=PremiumUI.main_menu(), parse_mode="Markdown")
    elif update.callback_query and is_new:
        await update.callback_query.message.reply_text(text, reply_markup=PremiumUI.main_menu(), parse_mode="Markdown")
        
