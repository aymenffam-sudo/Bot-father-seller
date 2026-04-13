import subprocess, sys, json, os, signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

MASTER_TOKEN = "8593915208:AAHTLNiwLsN8uonzRRoP4CJsWgjYvC8IEPY"
OWNER_ID = 6676819684
BOTS_DATA = "active_bots.json"

def load_db():
    if not os.path.exists(BOTS_DATA): return {}
    with open(BOTS_DATA, "r") as f: return json.load(f)

def save_db(data):
    with open(BOTS_DATA, "w") as f: json.dump(data, f)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    btns = [[InlineKeyboardButton("🚀 صنع بوتي الخاص", callback_data="new")]]
    if uid in db: btns.append([InlineKeyboardButton("⚙️ إدارة بوتي", callback_data="manage")])
    await update.message.reply_text("**مرحباً بك في مصنع بوتات Ben 10 🍀**", reply_markup=InlineKeyboardMarkup(btns))

async def control_bot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    db = load_db()
    
    if query.data == "run":
        if db[uid]["status"] == "running": return
        p = subprocess.Popen([sys.executable, "store_bot.py", db[uid]["token"], uid])
        db[uid].update({"pid": p.pid, "status": "running"})
    elif query.data == "stop":
        if db[uid]["pid"]:
            try: os.kill(db[uid]["pid"], signal.SIGTERM)
            except: pass
        db[uid].update({"pid": None, "status": "stopped"})
    
    save_db(db)
    # تحديث واجهة الإدارة
    status = "🟢 يعمل" if db[uid]["status"] == "running" else "🔴 متوقف"
    btns = [[InlineKeyboardButton("▶️ تشغيل", callback_data="run"), InlineKeyboardButton("⏹ إيقاف", callback_data="stop")]]
    await query.message.edit_text(f"⚙️ إدارة البوت:\nالحالة: {status}", reply_markup=InlineKeyboardMarkup(btns))

def main():
    app = ApplicationBuilder().token(MASTER_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(control_bot, pattern="^(run|stop)$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^manage$")) # أضف منطق العرض
    # إضافة ConversationHandler لاستلام التوكن هنا...
    app.run_polling()

if __name__ == "__main__":
    main()
