import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import threading
import time

# --- الإعدادات المباشرة ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o' 
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com'

# إعداد البوت و Gemini
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة المحادثات
chat_sessions = {}

app = Flask(__name__)

# --- الحل الجذري: ربط الـ Webhook عند تشغيل السيرفر مباشرة ---
# وضعناها خارج الـ "main" لكي تعمل مع Gunicorn
try:
    bot.remove_webhook()
    time.sleep(1) # انتظار ثانية للتأكد من الحذف
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    print("✅ Webhook was set successfully!")
except Exception as e:
    print(f"❌ Error setting webhook: {e}")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # تشغيل المعالجة في الخلفية
        threading.Thread(target=bot.process_new_updates, args=([update],)).start()
        
        return "!", 200
    else:
        return "Error", 403

@app.route("/")
def index():
    return "<h1>Bot is Running!</h1>", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, 'typing')
        
        if chat_id not in chat_sessions:
            chat_sessions[chat_id] = model.start_chat(history=[])
        
        chat_session = chat_sessions[chat_id]
        response = chat_session.send_message(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "لم أستطع توليد رد، حاول مرة أخرى.")
            
    except Exception as e:
        print(f"Detailed Error: {e}") # سيظهر هذا في الـ Logs عند حدوث خطأ
        bot.reply_to(message, "حدث خطأ في معالجة الرسالة.")

# ملاحظة: لا حاجة لـ app.run هنا لأن Render يستخدم gunicorn
