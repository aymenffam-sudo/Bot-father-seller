import subprocess, sys, json, os, signal, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# --- الإعدادات ---
MASTER_TOKEN = "8789785920:AAGWXPlRprQGiJJYQ4dfY60Z-M_VWcY_EUQ"
OWNER_ID = 6676819684
WAITING_TOKEN = 1
DB = "active_bots.json"

logging.basicConfig(level=logging.INFO)

def load_db():
    if not os.path.exists(DB): 
        with open(DB, "w") as f: json.dump({}, f)
        return {}
    try:
        with open(DB, "r") as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB, "w") as f: json.dump(data, f)

# ── القائمة الرئيسية ──
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    keyboard = [[InlineKeyboardButton("🚀 صنع بوتي الخاص", callback_data="new")]]
    if uid in db:
        keyboard.append([InlineKeyboardButton("⚙️ إدارة بوتي", callback_data="manage")])
    
    await update.message.reply_text(
        "**🍀 مرحباً بك في مصنع بوتات Ben 10**\n\nاضغط على الزر أدناه لبدء إنشاء بوتك الشخصي.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ── مرحلة طلب التوكن ──
async def ask_token(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📥 **أرسل الآن توكن بوتك من @BotFather:**\n\n(لإلغاء العملية أرسل /cancel)")
    return WAITING_TOKEN

async def save_new_bot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, token = str(update.effective_user.id), update.message.text.strip()
    
    if ":" not in token:
        await update.message.reply_text("❌ التوكن غير صحيح، تأكد من إرسال التوكن كاملاً.")
        return WAITING_TOKEN

    db = load_db()
    db[uid] = {"token": token, "status": "stopped", "pid": None}
    save_db(db)
    
    await update.message.reply_text("✅ **تم ربط البوت بنجاح!**\nأرسل /start الآن للدخول إلى لوحة التحكم وتشغيله.")
    return ConversationHandler.END

# ── إلغاء العملية ──
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(MASTER_TOKEN).build()

    # نظام المحادثة لصنع البوت
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_token, pattern="^new$")],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_bot)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    # هنا يمكنك إضافة معالج أزرار الإدارة (تشغيل/إيقاف) كما في الأكواد السابقة

    print("🚀 بوت الأب المصلح يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
