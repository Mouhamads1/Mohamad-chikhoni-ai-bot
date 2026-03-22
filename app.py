import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- الإعدادات ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o'
URL = 'https://your-app-name.onrender.com/' # سنغير هذا لاحقاً برابط الاستضافة

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# قاموس لتخزين سياق المحادثة لكل مستخدم (ذاكرة مؤقتة)
chat_sessions = {}

app = Flask(__name__)

# استقبال التنبيهات من تليجرام
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL + TOKEN)
    return "البوت يعمل بنظام Webhook!", 200

# --- منطق البوت الذكي ---
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_id = message.chat.id
    
    # إذا كان المستخدم جديداً، نفتح له جلسة محادثة جديدة
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        bot.send_chat_action(user_id, 'typing')
        # إرسال الرسالة مع الاحتفاظ بالسياق
        response = chat_sessions[user_id].send_message(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "حدث خطأ ما، جرب لاحقاً.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
