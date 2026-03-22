import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import threading
import time

# --- الإعدادات ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o'
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com'

# إعداد البوت و Gemini
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة المحادثة (ستعمل بشكل أفضل إذا ضبطت عدد الـ Workers إلى 1 في Render)
chat_sessions = {}

app = Flask(__name__)

# --- تفعيل الربط فور تشغيل التطبيق (هام جداً لـ Render) ---
def init_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{URL}/{TOKEN}")
        print("✅ Webhook Set Successfully!")
    except Exception as e:
        print(f"❌ Webhook Error: {e}")

# استدعاء الدالة هنا لضمان عملها مع Gunicorn
init_webhook()

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # استخدام Thread لمعالجة الرسالة في الخلفية وتجنب خطأ الـ Timeout (104)
        threading.Thread(target=bot.process_new_updates, args=([update],)).start()
        
        return "!", 200
    return "Error", 403

@app.route("/")
def index():
    return "Bot is active!", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, 'typing')
        
        # التحقق من وجود جلسة سابقة
        if chat_id not in chat_sessions:
            chat_sessions[chat_id] = model.start_chat(history=[])
        
        chat_session = chat_sessions[chat_id]
        response = chat_session.send_message(message.text)
        
        if response and response.text:
            bot.reply_to(message, response.text)
            
    except Exception as e:
        print(f"🔥 Error in handle_chat: {e}")
        # إذا حدث خطأ في الذاكرة، نمسحها ونرد برد بسيط
        chat_sessions.pop(chat_id, None)
        try:
            res = model.generate_content(message.text)
            bot.reply_to(message, res.text)
        except:
            bot.reply_to(message, "عذراً، حدث خطأ في الاتصال بـ Gemini. حاول مرة أخرى.")

# هذا السطر مهم فقط للتجربة المحلية، Render سيتجاهله ويستخدم Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
