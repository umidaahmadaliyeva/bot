import logging
import os

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
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
if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

REQUIRED_CHANNELS = [
    "@piramida_2024",
    "@piramidaschool",
]

DATA_CHANNEL = "@datapiramida"

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== STATES ==================
SCHOOL, CLASS_GRADE, FULL_NAME, PHONE = range(4)

# ================== SUB CHECK ==================
async def check_subscription(user_id: int, bot) -> bool:
    try:
        for channel in REQUIRED_CHANNELS:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        return True
    except Exception as e:
        logger.error(f"Sub check error: {e}")
        return False

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(user.id, context.bot):
        buttons = [
            [InlineKeyboardButton("📢 1-kanal", url="https://t.me/piramida_2024")],
            [InlineKeyboardButton("📢 2-kanal", url="https://t.me/piramidaschool")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")],
        ]
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun **ikkala kanalga ham obuna bo‘ling**:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )
        return ConversationHandler.WAITING

    return await ask_school(update, context)

# ================== CALLBACK ==================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_subscription(query.from_user.id, context.bot):
        await query.message.reply_text("❌ Hali barcha kanallarga obuna bo‘lmadingiz.")
        return ConversationHandler.WAITING

    return await ask_school(update, context)

# ================== COMMON ==================
async def ask_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    context.user_data.clear()
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = user.username

    if update.message:
        await update.message.reply_text(
            "Siz qaysi maktab o‘quvchisisiz?",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.callback_query.message.reply_text(
            "✅ Obuna tasdiqlandi!\n\nSiz qaysi maktab o‘quvchisisiz?",
            reply_markup=ReplyKeyboardRemove(),
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

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Telefon raqamingizni yuboring 👇",
        reply_markup=keyboard,
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.contact:
        await update.message.reply_text("❗ Iltimos, tugma orqali telefon yuboring.")
        return PHONE

    context.user_data["phone"] = update.message.contact.phone_number
    data = context.user_data

    text = (
        "🧾 *Yangi ishtirokchi*\n\n"
        f"👤 Ism: {data['full_name']}\n"
        f"🏫 Maktab: {data['school']}\n"
        f"📚 Sinf: {data['class_grade']}\n"
        f"📞 Telefon: `{data['phone']}`\n"
        f"🆔 Telegram ID: `{data['telegram_id']}`\n"
        f"👤 Username: @{data['username']}" if data.get("username") else "—"
    )

    await context.bot.send_message(
        chat_id=DATA_CHANNEL,
        text=text,
        parse_mode="Markdown",
    )

    await update.message.reply_text(
        "✅ Ma’lumotlaringiz qabul qilindi.\nOmad! 🍀\nQo'shimcha ma'lumot uchun 📞 +998 77 256 19 26\n➡️@Mathematics26_A",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"),
        ],
        states={
            SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_school)],
            CLASS_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_class)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, receive_phone)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(conv)

    logger.info("Bot ishga tushdi 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
