import sys, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler, ConversationHandler
)

# --- إعدادات البوت الفرعي (تلقائية من الأب) ---
if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    OWNER_ID = int(sys.argv[2])
else:
    BOT_TOKEN = "TOKEN_HERE"
    OWNER_ID = 6676819684

DB_FILE = f"db_{BOT_TOKEN.split(':')[0]}.json"
FOOTER = "\n\n*Ben 10 🍀*"

# حالات الانتظار (States) لعمليات الإدخال
WAIT_BC, WAIT_SUB, WAIT_ADD_PTS, WAIT_ADD_AD, WAIT_COUPON = range(5)

logging.basicConfig(level=logging.INFO)

# --- إدارة قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {}, "admins": [], "owners": [OWNER_ID], 
            "coupons": {}, "prices": {"منتج 1": 100}, 
            "sub_channel": "@YourChannel"
        }
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return load_db()

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- التحقق من الاشتراك الإجباري ---
async def check_sub(update, ctx, channel_id):
    try:
        member = await ctx.bot.get_chat_member(channel_id, update.effective_user.id)
        return member.status not in ['left', 'kicked']
    except: return True

# --- القائمة الرئيسية ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    if uid not in db["users"]:
        db["users"][uid] = {"points": 0, "balance": 0}
        if ctx.args:
            ref_id = ctx.args[0]
            if ref_id in db["users"] and ref_id != uid:
                db["users"][ref_id]["points"] += 1
    save_db(db)

    # فحص الاشتراك الإجباري
    if not await check_sub(update, ctx, db["sub_channel"]):
        btn = [[InlineKeyboardButton("📢 اشترك هنا", url=f"https://t.me/{db['sub_channel'][1:]}")],
               [InlineKeyboardButton("✅ تم الاشتراك", callback_data="start_cmd")]]
        await update.message.reply_text(f"⚠️ *يجب عليك الانضمام لقناتنا أولاً لاستخدام البوت:*\n{db['sub_channel']}", 
                                       reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        return

    btns = [
        [InlineKeyboardButton("👤 حسابي", callback_data="my_acc"), InlineKeyboardButton("🎁 المتجر", callback_data="shop")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="ref_link"), InlineKeyboardButton("🎫 كوبون", callback_data="coupon")],
    ]
    
    if int(uid) in db["owners"] or int(uid) in db["admins"]:
        btns.append([InlineKeyboardButton("🛠 لوحة التحكم", callback_data="admin_panel")])

    text = f"*👋 أهلاً بك في المتجر الشامل!*\n\nنقاطك الحالية: `{db['users'][uid]['points']}`" + FOOTER
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

# --- معالج الأزرار ولوحة التحكم ---
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()

    if query.data == "start_cmd":
        await start(update, ctx)

    elif query.data == "my_acc":
        pts = db["users"].get(uid, {}).get("points", 0)
        await query.edit_message_text(f"👤 *معلومات حسابك:*\n\n🔹 *النقاط:* {pts}\n🔹 *الآيدي:* `{uid}`" + FOOTER, 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    elif query.data == "ref_link":
        bot_user = (await ctx.bot.get_me()).username
        link = f"https://t.me/{bot_user}?start={uid}"
        await query.edit_message_text(f"🔗 *رابط الدعوة الخاص بك:*\n\n`{link}`\n\n🎁 *احصل على نقطة مقابل كل دعوة!*" + FOOTER, 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]]), parse_mode="Markdown")

    # --- لوحة التحكم الشاملة ---
    elif query.data == "admin_panel":
        is_owner = int(uid) in db["owners"]
        is_admin = int(uid) in db["admins"]

        if not is_owner and not is_admin: return

        if is_owner:
            btns = [
                [InlineKeyboardButton("📢 إذاعة", callback_data="bc"), InlineKeyboardButton("🎫 كوبون", callback_data="make_c")],
                [InlineKeyboardButton("👤 إضافة أدمن", callback_data="add_ad"), InlineKeyboardButton("👑 إضافة أونر", callback_data="add_ow")],
                [InlineKeyboardButton("💰 إضافة نقاط", callback_data="add_pts_all"), InlineKeyboardButton("♻️ تصفير النقاط", callback_data="reset_pts")],
                [InlineKeyboardButton("📢 تعديل الاشتراك", callback_data="edit_sub"), InlineKeyboardButton("⚙️ الأسعار", callback_data="edit_pr")],
                [InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="start_cmd")]
            ]
            title = "👑 *لوحة التحكم الشاملة (الأونر)*"
        else:
            btns = [
                [InlineKeyboardButton("🎫 صنع كوبون", callback_data="make_c")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data="start_cmd")]
            ]
            title = "🛠 *لوحة تحكم الأدمن*"

        await query.edit_message_text(f"{title}\n\nاختر من الخيارات المتاحة لك:" + FOOTER, 
                                     reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

    # وظيفة تصفير النقاط السريعة
    elif query.data == "reset_pts":
        if int(uid) in db["owners"]:
            for u in db["users"]: db["users"][u]["points"] = 0
            save_db(db)
            await query.answer("✅ تم تصفير نقاط الجميع!", show_alert=True)
            await start(update, ctx)

# --- تشغيل البوت ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print(f"✅ تم تشغيل بوت المتجر بنجاح للمالك: {OWNER_ID}")
    app.run_polling()

if __name__ == "__main__":
    main()
