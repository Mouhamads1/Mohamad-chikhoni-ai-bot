import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- الإعدادات (تأكد من نسخها بدقة من BotFather و Google Studio) ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o'
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com'

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

chat_sessions = {}
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"خطأ في استقبال الرسالة: {e}")
        return "Error", 500

@app.route("/")
def index():
    return "السيرفر يعمل، والبوت ينتظر الرسائل!", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_id = message.chat.id
    print(f"وصلت رسالة من {user_id}: {message.text}") # سيظهر هذا في الـ Logs
    
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    try:
        bot.send_chat_action(user_id, 'typing')
        # محاولة الحصول على رد من Gemini
        response = model.generate_content(message.text) 
        print(f"رد الذكاء الاصطناعي: {response.text}") # سيظهر في الـ Logs
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"خطأ في الذكاء الاصطناعي أو تليجرام: {e}") # هذا هو السطر الأهم!
        bot.reply_to(message, "عذراً، لدي مشكلة في الاتصال بمخي (الذكاء الاصطناعي).")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
