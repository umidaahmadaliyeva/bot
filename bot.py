import logging
import os

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ================== ENV ==================
TOKEN = os.getenv("BOT_TOKEN")

# 🔔 OBUNA TEKSHIRILADIGAN KANAL
SUBSCRIBE_CHANNEL = "@kh_journey"

# 🧾 MAʼLUMOT TASHLANADIGAN KANAL
DATA_CHANNEL = "@datapiramida"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== STATES ==================
SCHOOL, CLASS_GRADE, FULL_NAME = range(3)

# ================== SUB CHECK ==================
async def check_subscription(user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(SUBSCRIBE_CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(user.id, context.bot):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Kanalga obuna bo‘lish",
                    url=f"https://t.me/{SUBSCRIBE_CHANNEL.lstrip('@kh_journey')}"
                )
            ],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling:",
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
    data = context.user_data

    text = (
        "🧾 *Yangi ishtirokchi*\n\n"
        f"👤 Ism: {data['full_name']}\n"
        f"🏫 Maktab: {data['school']}\n"
        f"📚 Sinf: {data['class_grade']}\n"
        f"🆔 Telegram ID: `{data['telegram_id']}`\n"
        f"👤 Username: @{data['username']}" if data.get("username") 
    )

    # 🔥 AYNAN @datapiramida KANALIGA YUBORISH
    try:
        await context.bot.send_message(
            chat_id=DATA_CHANNEL,
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Kanalga yuborishda xato: {e}")

    await update.message.reply_text(
        "✅ Ma’lumotlaringiz qabul qilindi.\nOmad! 🍀"
    )
    return ConversationHandler.END

# ================== MAIN ==================
def main():
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
