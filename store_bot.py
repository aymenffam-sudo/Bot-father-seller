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

# حالات الانتظار للمدخلات (States)
WAIT_BC, WAIT_ADD_PTS, WAIT_ADD_AD = range(3)

logging.basicConfig(level=logging.INFO)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "admins": [], "owners": [OWNER_ID], "coupons": {}, "sub_channel": "@YourChannel"}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return load_db()

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

    text = f"*👋 أهلاً بك في المتجر!*" + FOOTER
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    return ConversationHandler.END

# --- معالج الأزرار ---
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()

    if query.data == "start_cmd":
        return await start(update, ctx)

    elif query.data == "my_acc":
        pts = db["users"].get(uid, {}).get("points", 0)
        await query.edit_message_text(f"👤 *حسابك:*\n🔹 نقاطك: `{pts}`", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "admin_panel":
        is_owner = int(uid) in db["owners"]
        is_admin = int(uid) in db["admins"]
        if not is_owner and not is_admin: return

        # لوحة الأدمن (تعديل الرسالة)
        admin_btns = [[InlineKeyboardButton("🎫 صنع كوبون", callback_data="make_c")], [InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]
        await query.edit_message_text("🛠 *لوحة الإدارة:*", reply_markup=InlineKeyboardMarkup(admin_btns), parse_mode="Markdown")

        # لوحة الأونر (رسالة جديدة)
        if is_owner:
            owner_btns = [
                [InlineKeyboardButton("📢 إذاعة", callback_data="start_bc"), InlineKeyboardButton("👤 إضافة أدمن", callback_data="start_add_ad")],
                [InlineKeyboardButton("💰 شحن نقاط", callback_data="start_add_pts"), InlineKeyboardButton("♻️ تصفير النقاط", callback_data="reset_all")]
            ]
            await ctx.bot.send_message(chat_id=uid, text="👑 *لوحة الأونر الشاملة:*", reply_markup=InlineKeyboardMarkup(owner_btns), parse_mode="Markdown")

    elif query.data == "reset_all":
        if int(uid) in db["owners"]:
            for u in db["users"]: db["users"][u]["points"] = 0
            save_db(db)
            await query.answer("✅ تم التصفير", show_alert=True)

# --- وظائف الإدخال (الإذاعة والشحن) ---
async def start_bc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📢 *أرسل رسالة الإذاعة الآن:*", parse_mode="Markdown")
    return WAIT_BC

async def do_bc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    text = update.message.text
    count = 0
    for user_id in db["users"]:
        try:
            await ctx.bot.send_message(chat_id=user_id, text=f"📢 *إعلان جديد:*\n\n{text}", parse_mode="Markdown")
            count += 1
        except: continue
    await update.message.reply_text(f"✅ تم الإرسال لـ {count} مستخدم.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # استخدام ConversationHandler لربط الأزرار التي تحتاج إدخال نصي
    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_bc, pattern="^start_bc$"),
            # يمكنك إضافة entry_points لشحن النقاط هنا بنفس الطريقة
        ],
        states={
            WAIT_BC: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_bc)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()

if __name__ == "__main__":
    main()
