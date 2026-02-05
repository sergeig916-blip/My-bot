import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🚂 Бот запущен на Railway! Привет!')

def main():
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("ERROR: BOT_TOKEN не найден!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Бот запускается...")
    app.run_polling()

if __name__ == '__main__':
    main()
    def main():
    # ВРЕМЕННО: токен прямо в коде
    BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"  # Вставьте ваш токен
    
    # Или оставьте получение из переменных окружения:
    # BOT_TOKEN = os.getenv('BOT_TOKEN') or "ВАШ_ТОКЕН_ЗДЕСЬ"
    
    if not BOT_TOKEN:
        logger.error("ERROR: BOT_TOKEN не найден!")
        return