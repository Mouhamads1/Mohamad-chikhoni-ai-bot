import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- الإعدادات ---
TOKEN = '8772661692:AAFZP4n3IRvQmzFlc4_ISM66jvk2oYGFG7c'
GEMINI_KEY = 'AIzaSyCKPWMPDFOaUMIstOABvQPw2GvsTZyI93o' 
URL = 'https://mohamad-chikhoni-ai-bot.onrender.com'

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "السيرفر يعمل بنجاح!", 200

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # تجربة إرسال مباشر بدون chat_session لتفادي أخطاء الذاكرة مؤقتاً
        response = model.generate_content(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "استلمت رسالتك لكن لم أستطع تكوين رد.")
            
    except Exception as e:
        # هذا السطر سيطبع لك الخطأ الحقيقي في Render Logs
        print(f"ERROR: {str(e)}")
        bot.reply_to(message, f"حدث خطأ فني: {str(e)[:50]}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
