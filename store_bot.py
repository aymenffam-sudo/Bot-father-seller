import sys, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
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

logging.basicConfig(level=logging.INFO)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "admins": [], "owners": [OWNER_ID], "coupons": {}, "sub_channel": "@YourChannel"}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return load_db()

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    if uid not in db["users"]:
        db["users"][uid] = {"points": 0}
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

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    db = load_db()

    if query.data == "start_cmd":
        await start(update, ctx)

    elif query.data == "admin_panel":
        is_owner = int(uid) in db["owners"]
        is_admin = int(uid) in db["admins"]

        if not is_owner and not is_admin: return

        # 1. الرسالة الأولى: لوحة الإدارة العادية (تعديل الرسالة الحالية)
        admin_btns = [
            [InlineKeyboardButton("🎫 صنع كوبون", callback_data="make_c")],
            [InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="start_cmd")]
        ]
        await query.edit_message_text("🛠 *لوحة إدارة المتجر (العامة):*", reply_markup=InlineKeyboardMarkup(admin_btns), parse_mode="Markdown")

        # 2. الرسالة الثانية: لوحة الأونر الشاملة (رسالة جديدة تماماً تصل للأونر فقط)
        if is_owner:
            owner_btns = [
                [InlineKeyboardButton("📢 إذاعة للكل", callback_data="bc"), InlineKeyboardButton("👑 إضافة أونر", callback_data="add_ow")],
                [InlineKeyboardButton("👤 إضافة أدمن", callback_data="add_ad"), InlineKeyboardButton("⚙️ تعديل الأسعار", callback_data="edit_pr")],
                [InlineKeyboardButton("💰 شحن نقاط", callback_data="add_pts"), InlineKeyboardButton("♻️ تصفير النقاط", callback_data="reset_all")],
                [InlineKeyboardButton("📢 تعديل الإشتراك", callback_data="edit_sub")]
            ]
            # نستخدم bot.send_message لإرسال رسالة جديدة منفصلة
            await ctx.bot.send_message(
                chat_id=uid,
                text="👑 *لوحة التحكم الشاملة (خاصة بالأونر فقط):*\n\nهذه الرسالة تحتوي على صلاحياتك الكاملة لإدارة النظام." + FOOTER,
                reply_markup=InlineKeyboardMarkup(owner_btns),
                parse_mode="Markdown"
            )

    elif query.data == "reset_all":
        if int(uid) in db["owners"]:
            for u in db["users"]: db["users"][u]["points"] = 0
            save_db(db)
            await query.answer("✅ تم تصفير نقاط الجميع بنجاح!", show_alert=True)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
