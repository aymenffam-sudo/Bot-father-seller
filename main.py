import telebot
import time
import random
from instagram_private_api import Client

# --- الإعدادات ---
API_TOKEN = '8709471554:AAFBzzpM3OHhZNHte_sA3iJ7mJ-Xyo8-NyE'
OWNER_ID = 6676819684  # الأيدي حقك عشان ما حد غيرك يتحكم بالبوت
bot = telebot.TeleBot(API_TOKEN)

# قائمة الاستثناءات (الناس اللي ما تبي تحذفهم)
WHITELIST = ["", "f_v_8"]

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(message, "أهلاً بك! أرسل بيانات الإنستغرام بهذا الشكل:\n`user:pass`\n\n*تنبيه: سيتم الحذف ببطء لتجنب الحظر.*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: ":" in m.text)
def start_unfollow(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        insta_user, insta_pass = message.text.split(":")
        bot.send_message(OWNER_ID, f"🔄 جاري تسجيل الدخول إلى {insta_user}...")
        
        api = Client(insta_user, insta_pass)
        user_id = api.authenticated_user_id
        
        # جلب المتابعين
        bot.send_message(OWNER_ID, "🔎 جاري فحص قائمة المتابعة...")
        following = api.user_following(user_id, rank_token=api.generate_uuid())
        users_to_process = following.get("users", [])

        bot.send_message(OWNER_ID, f"📊 وجدنا {len(users_to_process)} متابع. نبدأ التنظيف؟")

        for user in users_to_process:
            u_name = user["username"]
            u_id = user["pk"]

            if u_name in WHITELIST:
                bot.send_message(OWNER_ID, f"🛡️ تخطي (قائمة بيضاء): {u_name}")
                continue

            # عملية الحذف
            api.friendships_destroy(u_id)
            bot.send_message(OWNER_ID, f"✅ تم إلغاء متابعة: @{u_name}")

            # تأخير عشوائي طويل (مهم جداً للسلامة)
            wait = random.randint(40, 90) 
            time.sleep(wait)

        bot.send_message(OWNER_ID, "🏁 انتهت العملية بنجاح!")

    except Exception as e:
        bot.send_message(OWNER_ID, f"❌ خطأ: {str(e)}")

print("Bot is running...")
bot.polling()
