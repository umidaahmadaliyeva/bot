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

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN yo‘q")

REQUIRED_CHANNELS = ["@piramida_2024", "@piramidaschool"]
DATA_CHANNEL = "@datapiramida"

logging.basicConfig(level=logging.INFO)

SCHOOL, CLASS_GRADE, FULL_NAME, PHONE = range(4)

# ================= SUB CHECK =================
async def check_subscription(user_id: int, bot) -> bool:
    try:
        for ch in REQUIRED_CHANNELS:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        return True
    except:
        return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(user.id, context.bot):
        kb = [
            [InlineKeyboardButton("📢 1-kanal", url="https://t.me/piramida_2024")],
            [InlineKeyboardButton("📢 2-kanal", url="https://t.me/piramidaschool")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")],
        ]
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun ikkala kanalga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return ConversationHandler.END

    return await ask_school(update, context)

# ================= CALLBACK =================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_subscription(query.from_user.id, context.bot):
        await query.message.reply_text("❌ Hali obuna to‘liq emas.")
        return ConversationHandler.END

    return await ask_school(update, context)

# ================= COMMON =================
async def ask_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = user.username

    text = "Siz qaysi maktab o‘quvchisisiz?"

    if update.message:
        await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.callback_query.message.reply_text(text, reply_markup=ReplyKeyboardRemove())

    return SCHOOL

# ================= STEPS =================
async def receive_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["school"] = update.message.text
    await update.message.reply_text("Siz nechinchi sinf o‘quvchisisiz?")
    return CLASS_GRADE

async def receive_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["class"] = update.message.text
    await update.message.reply_text("Ism va familiyangizni kiriting:")
    return FULL_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Telefon raqamingizni yuboring 👇",
        reply_markup=kb,
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.contact:
        await update.message.reply_text("❗ Telefonni tugma orqali yuboring.")
        return PHONE

    context.user_data["phone"] = update.message.contact.phone_number
    d = context.user_data

    text = (
        "🧾 *Yangi ishtirokchi*\n\n"
        f"👤 Ism: {d['name']}\n"
        f"🏫 Maktab: {d['school']}\n"
        f"📚 Sinf: {d['class']}\n"
        f"📞 Telefon: `{d['phone']}`\n"
        f"🆔 ID: `{d['telegram_id']}`"
    )

    await context.bot.send_message(DATA_CHANNEL, text, parse_mode="Markdown")

    await update.message.reply_text(
        "✅ Ma’lumotlaringiz qabul qilindi!",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END

# ================= MAIN =================
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
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
