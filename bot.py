import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ Бот работает! Привет!')

def main():
    # 1. Сначала пробуем взять токен из Railway
    token = os.getenv('BOT_TOKEN')
    
    # 2. Если не нашли, используем этот (ЗАМЕНИТЕ НА СВОЙ!)
    if token is None:
        token = "8533684792:AAEX7st5kMflI-IL7XWOAohNhgODXzI12g8"  # ⬅️ ВСТАВЬТЕ ВАШ ТОКЕН СЮДА
    
    if not token:
        logger.error("❌ Токен не найден!")
        return
    
    try:
        # Создаем бота
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        
        logger.info("🚀 Запускаю бота...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")

if __name__ == '__main__':
    main()
