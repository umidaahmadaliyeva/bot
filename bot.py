import logging
import os
import datetime
import psycopg2

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ================== ENV ==================
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@kh_journey"

DB_URL = os.getenv("DB_URL")

if not all([TOKEN, DB_URL]):
    print("BOT_TOKEN =", TOKEN)
    print("DB_URL =", DB_URL)
    raise RuntimeError("Environment variables to‘liq emas!")

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== STATES ==================
SCHOOL, CLASS_GRADE, FULL_NAME = range(3)

# ================== POSTGRES ==================
def create_table_if_not_exists():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            username TEXT,
            school TEXT,
            class_grade TEXT,
            full_name TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_to_db(data: dict):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (telegram_id, username, school, class_grade, full_name)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data["telegram_id"],
        data.get("username", ""),
        data["school"],
        data["class_grade"],
        data["full_name"]
    ))
    conn.commit()
    cur.close()
    conn.close()

# ================== SUB CHECK ==================
async def check_subscription(user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(user.id, context.bot):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📢 Kanalga obuna bo‘lish",
                url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
            )],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun avval kanalga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = user.username

    await update.message.reply_text(
        "Siz qaysi maktab o‘quvchisisiz?",
        reply_markup=ReplyKeyboardRemove()
    )
    return SCHOOL

# ================== CALLBACK ==================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_subscription(query.from_user.id, context.bot):
        await query.message.reply_text("❌ Hali obuna bo‘lmagansiz.")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["telegram_id"] = query.from_user.id
    context.user_data["username"] = query.from_user.username

    await query.message.reply_text(
        "✅ Obuna tasdiqlandi!\n\nSiz qaysi maktab o‘quvchisisiz?"
    )
    return SCHOOL

# ================== STEPS ==================
async def receive_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["school"] = update.message.text.strip()
    await update.message.reply_text("Siz nechinchi sinf o‘quvchisisiz?")
    return CLASS_GRADE

async def receive_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["class_grade"] = update.message.text.strip()
    await update.message.reply_text("Ism va familiyangizni kiriting:")
    return FULL_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    save_to_db(context.user_data)

    await update.message.reply_text(
        "✅ Ma’lumotlaringiz saqlandi.\nOlimpiadada omad! 🍀"
    )
    return ConversationHandler.END

# ================== MAIN ==================
def main():
    create_table_if_not_exists()

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_school)],
            CLASS_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_class)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))

    logger.info("Bot ishga tushdi 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
