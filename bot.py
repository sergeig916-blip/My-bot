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
    # ВАРИАНТ 1: Если хотите временно вставить токен в код
    BOT_TOKEN = "ВСТАВЬТЕ_СЮДА_ВАШ_ТОКЕН"  # ⬅️ ЗАМЕНИТЕ НА ВАШ ТОКЕН
    
    # ВАРИАНТ 2: Если хотите брать из переменных окружения
    # BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("ERROR: BOT_TOKEN не найден!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Бот запускается...")
    app.run_polling()

if __name__ == '__main__':
    main()