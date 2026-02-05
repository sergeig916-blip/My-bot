import os
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await update.message.reply_text("✅ Бот работает!")

def main():
    token = os.getenv('BOT_TOKEN') or "ВАШ_ТОКЕН"
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()