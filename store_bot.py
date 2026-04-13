import sys, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler, ConversationHandler
)

# --- الإعدادات ---
if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    OWNER_ID = int(sys.argv[2])
else:
    BOT_TOKEN = "TOKEN_HERE"
    OWNER_ID = 6676819684

DB_FILE = f"db_{BOT_TOKEN.split(':')[0]}.json"
FOOTER = "\n\n*Ben 10 🍀*"

# حالات الانتظار (States)
WAIT_BC, WAIT_ADD_PTS, WAIT_SUB = range(3)

logging.basicConfig(level=logging.INFO)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "admins": [], "owners": [OWNER_ID], "sub_channel": "@YourChannel"}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"users": {}, "admins": [], "owners": [OWNER_ID], "sub_channel": "@YourChannel"}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- القائمة الرئيسية ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    if uid not in db["users"]: db["users"][uid] = {"points": 0}
    save_db(db)

    btns = [
        [InlineKeyboardButton("👤 حسابي", callback_data="my_acc"), InlineKeyboardButton("🎁 المتجر", callback_data="shop")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="ref_link"), InlineKeyboardButton("🎫 كوبون", callback_data="coupon")],
    ]
    if int(uid) in db["owners"] or int(uid) in db["admins"]:
        btns.append([InlineKeyboardButton("🛠 لوحة التحكم", callback_data="admin_panel")])

    text = f"*👋 أهلاً بك في متجر Ben 10*\n\nنقاطك: `{db['users'][uid]['points']}`" + FOOTER
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    return ConversationHandler.END

# --- معالجة الأزرار العادية ---
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()

    if query.data == "my_acc":
        pts = db["users"].get(uid, {}).get("points", 0)
        await query.edit_message_text(f"👤 *معلومات حسابك:*\n\n🔹 الآيدي: `{uid}`\n🔹 النقاط: `{pts}`", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "ref_link":
        bot_user = (await ctx.bot.get_me()).username
        await query.edit_message_text(f"🔗 *رابط دعوتك:*\n`https://t.me/{bot_user}?start={uid}`", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "admin_panel":
        is_owner = int(uid) in db["owners"]
        # لوحة الأدمن
        admin_btns = [[InlineKeyboardButton("🎫 صنع كوبون", callback_data="make_c")], [InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]
        await query.edit_message_text("🛠 *لوحة الإدارة العامة:*", reply_markup=InlineKeyboardMarkup(admin_btns), parse_mode="Markdown")
        # رسالة الأونر المنفصلة
        if is_owner:
            owner_btns = [
                [InlineKeyboardButton("📢 إذاعة للكل", callback_data="start_bc"), InlineKeyboardButton("💰 شحن نقاط", callback_data="start_add_pts")],
                [InlineKeyboardButton("♻️ تصفير النقاط", callback_data="reset_all"), InlineKeyboardButton("📢 تعديل الاشتراك", callback_data="start_edit_sub")]
            ]
            await ctx.bot.send_message(chat_id=uid, text="👑 *لوحة الأونر الشاملة:*", reply_markup=InlineKeyboardMarkup(owner_btns), parse_mode="Markdown")

    elif query.data == "reset_all":
        if int(uid) in db["owners"]:
            for u in db["users"]: db["users"][u]["points"] = 0
            save_db(db)
            await query.answer("✅ تم تصفير جميع النقاط", show_alert=True)

    elif query.data == "start_cmd":
        await start(update, ctx)

# --- دوال الإدخال (الإذاعة / الشحن / الاشتراك) ---
async def ask_for_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_bc":
        await query.message.reply_text("📢 *أرسل نص الإذاعة الآن:*", parse_mode="Markdown")
        return WAIT_BC
    elif query.data == "start_add_pts":
        await query.message.reply_text("💰 *أرسل الآيدي ثم مسافة ثم عدد النقاط:*\n(مثال: `6676819684 100`)", parse_mode="Markdown")
        return WAIT_ADD_PTS

async def do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    for user_id in db["users"]:
        try: await ctx.bot.send_message(user_id, f"📢 *إعلان جديد:*\n\n{update.message.text}", parse_mode="Markdown")
        except: continue
    await update.message.reply_text("✅ تم إرسال الإذاعة بنجاح!")
    return ConversationHandler.END

async def do_add_pts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target_id, amount = update.message.text.split()
        db = load_db()
        if target_id in db["users"]:
            db["users"][target_id]["points"] += int(amount)
            save_db(db)
            await update.message.reply_text(f"✅ تم إضافة {amount} نقطة للمستخدم {target_id}")
        else: await update.message.reply_text("❌ المستخدم غير موجود.")
    except: await update.message.reply_text("❌ خطأ في التنسيق. مثال: `12345 50` ")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # محادثة الإدارة (تسمع للأزرار التي تطلب إدخال)
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_input, pattern="^(start_bc|start_add_pts)$")],
        states={
            WAIT_BC: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
            WAIT_ADD_PTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_add_pts)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler)) # للأزرار العادية التي لا تتطلب نصاً
    
    app.run_polling()

if __name__ == "__main__":
    main()
