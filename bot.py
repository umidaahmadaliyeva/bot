import logging
import os
import datetime
from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from openpyxl import Workbook, load_workbook

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@kh_journey"   # majburiy obuna kanali
EXCEL_FILE = "data.xlsx"

# ================== LOGGING ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================== HOLATLAR ==================
SCHOOL, CLASS_GRADE, FULL_NAME = range(3)

# ================== KANALGA OBUNA TEKSHIRISH ==================
async def check_subscription(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================== EXCELGA SAQLASH ==================
def save_to_excel(data):
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append([
            "Vaqt", "Telegram ID", "Username",
            "Maktab", "Sinf", "Ism Familiya"
        ])
    else:
        wb = load_workbook(EXCEL_FILE)
        ws = wb.active

    ws.append([
        datetime.datetime.now(),
        data["telegram_id"],
        data["username"],
        data["school"],
        data["class_grade"],
        data["full_name"],
    ])

    wb.save(EXCEL_FILE)

# ================== /START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    is_subscribed = await check_subscription(user_id, context.bot)

    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="📢 Kanalga obuna bo‘lish",
                    url=f"https://t.me/kh_journey"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_sub"
                )
            ]
        ])

        await update.message.reply_text(
            "❗ Botdan foydalanish uchun avval kanalga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["telegram_id"] = user_id
    context.user_data["username"] = user.username

    await update.message.reply_text(
        "Siz qaysi maktab o‘quvchisisiz?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SCHOOL

# ================== CALLBACK: OBUNANI TEKSHIRISH ==================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    is_subscribed = await check_subscription(user.id, context.bot)

    if not is_subscribed:
        await query.message.reply_text(
            "❌ Siz hali kanalga obuna bo‘lmagansiz.\n"
            "Iltimos, obuna bo‘lib yana tekshiring."
        )
        return

    context.user_data.clear()
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = user.username

    await query.message.reply_text(
        "✅ Obuna muvaffaqiyatli tasdiqlandi!\n\n"
        "Siz qaysi maktab o‘quvchisisiz?"
    )

# ================== MAKTAB ==================
async def receive_school(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["school"] = update.message.text
    await update.message.reply_text("Siz nechinchi sinf o‘quvchisisiz?")
    return CLASS_GRADE

# ================== SINF ==================
async def receive_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["class_grade"] = update.message.text
    await update.message.reply_text("Ism va familiyangizni kiriting:")
    return FULL_NAME

# ================== ISM FAMILIYA ==================
async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text

    save_to_excel(context.user_data)

    await update.message.reply_text(
        "✅ Sizning ma’lumotlaringiz saqlandi.\n"
        "Olimpiadada omad tilaymiz!"
    )
    return ConversationHandler.END

# ================== BEKOR QILISH ==================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ro‘yxatdan o‘tish bekor qilindi.")
    return ConversationHandler.END

# ================== ASOSIY QISM ==================
def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_school)],
            CLASS_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_class)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(
        CallbackQueryHandler(check_sub_callback, pattern="check_sub")
    )

    application.run_polling()

if __name__ == "__bot__":
    bot()

if __name__ == "__main__":
    print("BOT_TOKEN mavjudmi?", TOKEN is not None)
    print("Polling boshlanmoqda...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        print("Polling xatosi:", str(e))
        import traceback
        traceback.print_exc()