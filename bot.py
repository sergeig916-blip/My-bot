import os
import logging
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('✅ Бот работает! Конфликт устранен.')

def main():
    # ВАШ ТОКЕН (замените!)
    token = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
    
    logger.info("🔄 Сбрасываю старое состояние бота...")
    
    # 1. Сбрасываем ВСЕ в Telegram API
    try:
        requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        requests.get(f"https://api.telegram.org/bot{token}/close", timeout=10)
        logger.info("✅ Telegram API сброшен")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сбросить API: {e}")
    
    # 2. Ждем
    time.sleep(3)
    
    # 3. Запускаем бота
    try:
        updater = Updater(token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        
        logger.info("🚀 Запускаю бота...")
        
        # Запуск с очисткой ВСЕГО
        updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            read_latency=10.0,
            allowed_updates=['message']
        )
        
        logger.info("🎉 Бот успешно запущен! Ошибок нет.")
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        # Если конфликт, ждем и пробуем еще раз
        if "Conflict" in str(e):
            logger.info("⏳ Жду 30 секунд и пробую еще раз...")
            time.sleep(30)
            main()  # рекурсивный перезапуск

if __name__ == '__main__':
    main()
