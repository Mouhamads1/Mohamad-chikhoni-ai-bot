import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import threading

# --- الإعدادات (المتغيرات المباشرة كما طلبت) ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o' 
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com'

# إعداد البوت و Gemini
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# قاموس لتخزين جلسات الدردشة (الذاكرة) لكل مستخدم بناءً على معرفه (chat_id)
chat_sessions = {}

app = Flask(__name__)

# دالة برمجية لربط البوت بالرابط (Webhook) تلقائياً عند تشغيل الكود
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    
    # حل مشكلة ConnectionResetError 104:
    # نقوم بمعالجة الرسالة في "خيط" (Thread) منفصل لكي نرد على تيليجرام فوراً بـ 200 OK
    threading.Thread(target=bot.process_new_updates, args=([update],)).start()
    
    return "!", 200

@app.route("/")
def index():
    return "السيرفر يعمل بنجاح والذاكرة مفعّلة!", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    chat_id = message.chat.id
    
    try:
        bot.send_chat_action(chat_id, 'typing')
        
        # --- نظام الذاكرة ---
        # إذا لم يكن للمستخدم جلسة سابقة، ننشئ له واحدة جديدة
        if chat_id not in chat_sessions:
            chat_sessions[chat_id] = model.start_chat(history=[])
        
        # إرسال الرسالة ضمن الجلسة (لكي يتذكر Gemini ما قيل سابقاً)
        chat_session = chat_sessions[chat_id]
        response = chat_session.send_message(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "استلمت رسالتك لكن لم أستطع تكوين رد.")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        # في حال حدوث خطأ في الجلسة (مثل امتلاء الذاكرة)، نقوم بمسحها ليعمل البوت مجدداً
        if chat_id in chat_sessions:
            del chat_sessions[chat_id]
        bot.reply_to(message, f"حدث خطأ فني بسيط، تم إعادة تشغيل الجلسة. حاول مرة أخرى.")

if __name__ == "__main__":
    # تشغيل ربط الWebhook
    set_webhook()
    # استخدام السيرفر المحلي للتجربة (في ريندير يفضل gunicorn)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
