# main.py
from telegram.ext import Application
from config import TELEGRAM_TOKEN
from database import init_db
from handlers import register_handlers

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    register_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()