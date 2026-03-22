import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import threading

# --- الإعدادات الآمنة (يتم جلبها من بيئة Render) ---
TOKEN = os.environ.get('8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c')
GEMINI_KEY = os.environ.get('AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o')
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com' # رابط تطبيقك

# إعداد البوت و Gemini
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة المحادثات لكل مستخدم
chat_sessions = {}

app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # --- الحل السحري لمشكلة الـ Connection Reset ---
        # نقوم بمعالجة الرد في "خلفية" السيرفر لكي لا ينتظر تيليجرام
        threading.Thread(target=bot.process_new_updates, args=([update],)).start()
        
        return "!", 200 # نرد فوراً بـ OK
    return "Forbidden", 403

@app.route("/")
def index():
    return "<h1>Bot is Online and Ready!</h1>", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    chat_id = message.chat.id
    try:
        # إظهار حالة "يكتب..." في تيليجرام
        bot.send_chat_action(chat_id, 'typing')
        
        # إدارة الذاكرة (History)
        if chat_id not in chat_sessions:
            chat_sessions[chat_id] = model.start_chat(history=[])
        
        chat_session = chat_sessions[chat_id]
        response = chat_session.send_message(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
            
    except Exception as e:
        print(f"Chat Error: {e}")
        # إذا حدث خطأ في الذاكرة، نمسحها ونحاول مرة أخرى كرسالة مفردة
        if chat_id in chat_sessions: del chat_sessions[chat_id]
        try:
            res = model.generate_content(message.text)
            bot.reply_to(message, res.text)
        except:
            bot.reply_to(message, "عذراً، Gemini مشغول حالياً. حاول ثانية.")

# تم حذف دالة set_webhook() لتجنب أخطاء 429 عند التشغيل
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
