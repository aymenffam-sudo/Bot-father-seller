import sys, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# إعدادات تلقائية من بوت الأب
if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    OWNER_ID = int(sys.argv[2])
else:
    BOT_TOKEN = "TOKEN_HERE"
    OWNER_ID = 6676819684

DB_FILE = f"db_{BOT_TOKEN.split(':')[0]}.json"
CHANNEL_ID = "@YourChannel" # يوزر قناتك
FOOTER = "\n\n**Ben 10 🍀**"

# --- إدارة قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "admins": [], "owners": [OWNER_ID], "coupons": {}, "prices": {"منتج_1": 50}}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- التحقق من الاشتراك ---
async def is_subbed(update, ctx):
    try:
        member = await ctx.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return member.status not in ['left', 'kicked']
    except: return True # لتجنب التوقف إذا لم يكن البوت أدمن

# --- الأوامر الرئيسية ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    if uid not in db["users"]:
        db["users"][uid] = {"points": 0, "balance": 0}
        if ctx.args: # نظام الإحالة (احلب أصدقاءك)
            ref_id = ctx.args[0]
            if ref_id in db["users"] and ref_id != uid:
                db["users"][ref_id]["points"] += 1
    save_db(db)

    if not await is_subbed(update, ctx):
        btn = [[InlineKeyboardButton("📢 اشترك هنا", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        await update.message.reply_text("❌ يجب الاشتراك بالقناة أولاً!", reply_markup=InlineKeyboardMarkup(btn))
        return

    btns = [
        [InlineKeyboardButton("👤 حسابي", callback_data="me"), InlineKeyboardButton("🎁 المتجر", callback_data="shop")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="ref"), InlineKeyboardButton("🎫 كوبون", callback_data="coupon")]
    ]
    if update.effective_user.id in db["owners"] or update.effective_user.id in db["admins"]:
        btns.append([InlineKeyboardButton("🛠 لوحة التحكم", callback_data="admin")])

    await update.message.reply_text(f"👋 أهلاً بك في المتجر!\nاستخدم الأزرار أدناه للتنقل." + FOOTER, 
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

# --- لوحة التحكم (رتب أونر وأدمن) ---
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    db = load_db()
    if uid not in db["owners"] and uid not in db["admins"]: return

    btns = [[InlineKeyboardButton("🎫 صنع كوبون", callback_data="make_c")]]
    if uid in db["owners"]:
        btns.append([InlineKeyboardButton("👤 إضافة أدمن", callback_data="add_ad"), InlineKeyboardButton("💰 الأسعار", callback_data="prc")])
        btns.append([InlineKeyboardButton("📢 إذاعة", callback_data="bc")])

    await update.callback_query.message.edit_text("🛠 لوحة الإدارة:", reply_markup=InlineKeyboardMarkup(btns))

# (يمكنك إضافة بقية منطق الكوبونات والأسعار هنا...)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin$"))
    app.run_polling()

if __name__ == "__main__":
    main()
