import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/health')
def health():
    return "OK"

# --- Настройки ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq использует OpenAI-совместимый API
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я ИИ-ассистент. Напиши мне любой вопрос — отвечу.\n"
        "Команда /help — список команд."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать\n"
        "/help — помощь\n"
        "Просто напиши сообщение — я отвечу через ИИ."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action(action="typing")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты дружелюбный помощник. Отвечай кратко и по делу."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Ой, что-то пошло не так. Попробуй ещё раз.")

def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)