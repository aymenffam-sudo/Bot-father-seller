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

# --- وظائف قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB): 
        with open(DB, "w") as f: json.dump({}, f)
        return {}
    try:
        with open(DB, "r") as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB, "w") as f: json.dump(data, f, indent=4)

# --- دالة التشغيل التلقائي (تنفذ عند إقلاع السيرفر) ---
async def on_startup(app):
    db = load_db()
    print("🔄 جاري التحقق من البوتات التي كانت تعمل...")
    for uid, info in db.items():
        if info.get("status") == "running":
            token = info.get("token")
            if token:
                print(f"🚀 إعادة تشغيل تلقائية للبوت: {uid}")
                # تشغيل البوت في الخلفية
                p = subprocess.Popen([sys.executable, "store_bot.py", token, uid])
                db[uid]["pid"] = p.pid
    save_db(db)

# --- الأوامر البرمجية ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    keyboard = [[InlineKeyboardButton("🚀 صنع بوتي الخاص", callback_data="new")]]
    if uid in db:
        keyboard.append([InlineKeyboardButton("⚙️ إدارة بوتي", callback_data="manage")])
    
    text = "*🍀 مصنع بوتات Ben 10*\n\nالبوت يدعم التشغيل التلقائي، بياناتك في أمان."
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def manage_my_bot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()
    
    status = "🟢 *يعمل*" if db[uid].get("status") == "running" else "🔴 *متوقف*"
    keyboard = [
        [InlineKeyboardButton("▶️ تشغيل", callback_data="run_bot"), InlineKeyboardButton("⏹ إيقاف", callback_data="stop_bot")],
        [InlineKeyboardButton("🗑 حذف البوت", callback_data="del_bot")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_home")]
    ]
    await query.edit_message_text(f"⚙️ *لوحة التحكم:*\n\nالحالة الحالية: {status}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_bot_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    db = load_db()
    
    if query.data == "run_bot":
        if db[uid].get("status") == "running":
            await query.answer("⚠️ يعمل بالفعل")
        else:
            p = subprocess.Popen([sys.executable, "store_bot.py", db[uid]["token"], uid])
            db[uid].update({"pid": p.pid, "status": "running"})
            save_db(db)
            await query.answer("🚀 تم التشغيل")
            
    elif query.data == "stop_bot":
        if db[uid].get("status") == "stopped":
            await query.answer("⚠️ متوقف بالفعل")
        else:
            try: os.kill(db[uid]["pid"], signal.SIGTERM)
            except: pass
            db[uid].update({"pid": None, "status": "stopped"})
            save_db(db)
            await query.answer("⏹ تم الإيقاف")
            
    elif query.data == "del_bot":
        db.pop(uid, None)
        save_db(db)
        return await start(update, ctx)

    return await manage_my_bot(update, ctx)

async def ask_token(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📥 *أرسل التوكن الخاص بك الآن:*", parse_mode="Markdown")
    return WAITING_TOKEN

async def save_new_bot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, token = str(update.effective_user.id), update.message.text.strip()
    db = load_db()
    db[uid] = {"token": token, "status": "stopped", "pid": None}
    save_db(db)
    await update.message.reply_text("✅ *تم الحفظ بنجاح!*", parse_mode="Markdown")
    return ConversationHandler.END

def main():
    # إضافة post_init لتشغيل دالة on_startup عند بداية تشغيل البوت
    app = ApplicationBuilder().token(MASTER_TOKEN).post_init(on_startup).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_token, pattern="^new$")],
        states={WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_bot)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(manage_my_bot, pattern="^manage$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_home$"))
    app.add_handler(CallbackQueryHandler(handle_bot_action, pattern="^(run_bot|stop_bot|del_bot)$"))

    print("🤖 بوت الأب الذكي يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
