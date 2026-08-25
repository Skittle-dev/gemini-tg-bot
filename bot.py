import os
import telebot
import requests

# Считываем секретные ключи из настроек Render (а не из текста кода!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_history = {}

def ask_gemini(user_id, text):
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "parts": [{"text": text}]})

    # Используем модель gemini-1.5-flash или последнюю доступную версию
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": user_history[user_id]}

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
        user_history[user_id].append({"role": "model", "parts": [{"text": ai_text}]})
        return ai_text
    else:
        user_history[user_id].pop()
        return f"Ошибка API ({response.status_code}): {response.text}"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "Привет! Я бот с Gemini. Задай мне любой вопрос!")

@bot.message_handler(commands=['reset'])
def reset_cmd(message):
    user_id = message.from_user.id
    user_history[user_id] = []
    bot.reply_to(message, "🧠 Память очищена!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = ask_gemini(message.from_user.id, message.text)
    
    if len(answer) > 4000:
        for x in range(0, len(answer), 4000):
            bot.send_message(message.chat.id, answer[x:x+4000])
    else:
        bot.reply_to(message, answer)

bot.infinity_polling()
