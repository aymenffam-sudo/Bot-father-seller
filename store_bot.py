import sys, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)

# --- إعدادات البوت الفرعي (تلقائية من الأب) ---
if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    OWNER_ID = int(sys.argv[2])
else:
    BOT_TOKEN = "TOKEN_HERE"
    OWNER_ID = 6676819684

DB_FILE = f"db_{BOT_TOKEN.split(':')[0]}.json"
CHANNEL_ID = "@YourChannel" # استبدله بيوزر قناتك (مثال: @ben10_store)
FOOTER = "\n\n*Ben 10 🍀*"

logging.basicConfig(level=logging.INFO)

# --- إدارة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "admins": [], "owners": [OWNER_ID], "coupons": {}, "prices": {"منتج 1": 100}}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"users": {}, "admins": [], "owners": [OWNER_ID], "coupons": {}, "prices": {"منتج 1": 100}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- التحقق من الاشتراك الإجباري ---
async def check_sub(update, ctx):
    try:
        member = await ctx.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return member.status not in ['left', 'kicked']
    except: return True # إذا لم يكن البوت أدمن في القناة سيتخطى الفحص

# --- القائمة الرئيسية ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    # تسجيل المستخدم الجديد ونظام الإحالة
    if uid not in db["users"]:
        db["users"][uid] = {"points": 0, "balance": 0}
        if ctx.args:
            ref_id = ctx.args[0]
            if ref_id in db["users"] and ref_id != uid:
                db["users"][ref_id]["points"] += 1 # نقطة لكل شخص
    save_db(db)

    # فحص الاشتراك
    if not await check_sub(update, ctx):
        btn = [[InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_ID[1:]}")],
               [InlineKeyboardButton("✅ تم الاشتراك", callback_data="start_cmd")]]
        await update.message.reply_text(f"⚠️ *عذراً! يجب الاشتراك في القناة أولاً:* {CHANNEL_ID}", 
                                       reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        return

    btns = [
        [InlineKeyboardButton("👤 حسابي", callback_data="my_acc"), InlineKeyboardButton("🎁 المتجر", callback_data="shop")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="ref_link"), InlineKeyboardButton("🎫 كوبون", callback_data="coupon")],
    ]
    
    # لوحة الإدارة للأدمن والأونر
    if int(uid) in db["owners"] or int(uid) in db["admins"]:
        btns.append([InlineKeyboardButton("🛠 لوحة التحكم", callback_data="admin_panel")])

    text = f"*👋 أهلاً بك {update.effective_user.first_name} في المتجر!*\n\nاستخدم الأزرار بالأسفل للتنقل بين الأقسام." + FOOTER
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

# --- معالج الأزرار (هذا ما كان ينقصك) ---
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()

    if query.data == "my_acc":
        pts = db["users"][uid]["points"]
        await query.edit_message_text(f"👤 *معلومات حسابك:*\n\n🔹 *النقاط:* {pts}\n🔹 *الآيدي:* `{uid}`" + FOOTER, 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "ref_link":
        bot_user = (await ctx.bot.get_me()).username
        link = f"https://t.me/{bot_user}?start={uid}"
        await query.edit_message_text(f"🔗 *رابط الدعوة الخاص بك:*\n\n`{link}`\n\n🎁 *احصل على نقطة مقابل كل صديق يدخل البوت!*" + FOOTER, 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "start_cmd":
        await start(update, ctx)

    # أضف هنا بقية شروط الأزرار (admin_panel, shop, الخ) بنفس الطريقة

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler)) # هذا السطر يربط كل الأزرار بالدالة
    
    app.run_polling()

if __name__ == "__main__":
    main()
