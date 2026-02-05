import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ Бот запущен и работает!')

def main():
    # Получаем токен
    TOKEN = os.getenv('BOT_TOKEN')
    
    # Если тестируете - можно вставить напрямую (удалите позже!)
    # TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
    
    if not TOKEN:
        logger.error("❌ Токен не найден!")
        return
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем команды
        app.add_handler(CommandHandler("start", start))
        
        # Запускаем
        logger.info("🚀 Запускаю бота...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")

if __name__ == '__main__':
    main()