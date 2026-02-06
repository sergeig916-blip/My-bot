import os
import logging
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ==========
# ... [ВСЯ СРЕДНЯЯ ЧАСТЬ КОДА ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ] ...
# Все функции и данные от start() до error_handler() остаются те же

def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запуск бота на Railway...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(show_maxes, pattern='^menu:maxes$'))
        application.add_handler(CallbackQueryHandler(show_week_menu, pattern='^menu:'))
        application.add_handler(CallbackQueryHandler(handle_day_selection, pattern='^day:'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Приложение создано и настроено")
        
        # Формируем правильный webhook URL
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        logger.info(f"🌐 Настройка webhook на: {webhook_url}")
        
        # Запускаем в режиме webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
