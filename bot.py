import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('✅ Бот работает!')

def main():
    token = os.getenv('BOT_TOKEN') or "8533684792:AAEX7st5kMflI-IL7XWOAohNhgODXzI12g8"
    
    if not token:
        logger.error("❌ Токен не найден!")
        return
    
    try:
        updater = Updater(token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        
        logger.info("🚀 Запускаю бота...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")

if __name__ == '__main__':
    main()
