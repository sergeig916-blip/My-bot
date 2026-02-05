import os
import logging
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('✅ Бот работает на Railway!')

def main():
    # ВАШ ТОКЕН СЮДА
    token = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"
    
    logger.info("🚀 Запускаю бота...")
    
    try:
        updater = Updater(token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        
        # Сбрасываем все старые сообщения
        updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            read_latency=5.0
        )
        
        logger.info("🎉 Бот успешно запущен!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")
        if "Conflict" in str(e):
            logger.info("⚠️ Конфликт. Жду 20 секунд...")
            time.sleep(20)
            # Пробуем еще раз
            main()

if __name__ == '__main__':
    main()
