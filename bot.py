import os
import logging
import asyncio
import json
import sys
from typing import Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # https://ваш-проект.railway.app/
PORT = int(os.environ.get("PORT", 8080))  # Railway использует порт из переменной PORT
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
def get_db_connection():
    """Создание подключения к базе данных"""
    if not DATABASE_URL:
        return None
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_database():
    """Инициализация таблиц в базе данных"""
    if not DATABASE_URL:
        logger.warning("⚠️ DATABASE_URL не указан, данные будут храниться в памяти")
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Таблица пользователей
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            bench_max DECIMAL DEFAULT 117.5,
            squat_max DECIMAL DEFAULT 125,
            deadlift_max DECIMAL DEFAULT 150,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица тренировочных недель
        cur.execute("""
        CREATE TABLE IF NOT EXISTS training_weeks (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            week_number INTEGER NOT NULL,
            completed_days JSONB DEFAULT '[]',
            weights_set BOOLEAN DEFAULT FALSE,
            week_weights JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, week_number)
        )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ База данных инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")

# ========== ДАННЫЕ ПО УМОЛЧАНИЮ ==========
# ... (остальной код остается БЕЗ ИЗМЕНЕНИЙ, вплоть до функции run_bot)

async def setup_webhook(application):
    """Настройка webhook"""
    if WEBHOOK_URL and WEBHOOK_URL.strip():
        # Убедимся, что URL начинается с https://
        webhook_url = WEBHOOK_URL.rstrip('/')
        if not webhook_url.startswith('http'):
            webhook_url = f'https://{webhook_url}'
        
        webhook_url = f"{webhook_url}/{BOT_TOKEN}"
        logger.info(f"🌐 Настройка webhook на: {webhook_url}")
        
        await application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info("✅ Webhook установлен")
        return True
    else:
        logger.warning("⚠️ WEBHOOK_URL не указан, webhook не настроен")
        return False

def run_bot():
    """Запуск бота - ОСНОВНАЯ ФУНКЦИЯ ДЛЯ RAILWAY"""
    logger.info("🚀 Запуск бота...")
    
    try:
        # Инициализируем базу данных
        init_database()
        
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(show_maxes, pattern='^menu:maxes$'))
        application.add_handler(CallbackQueryHandler(show_week_menu, pattern='^menu:'))
        application.add_handler(CallbackQueryHandler(handle_day_selection, pattern='^day:'))
        application.add_handler(CallbackQueryHandler(handle_weights_decision, pattern='^weights:'))
        application.add_handler(CallbackQueryHandler(handle_weight_change, pattern='^weight:change:'))
        application.add_handler(CallbackQueryHandler(handle_weight_skip, pattern='^weight:skip:'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Все обработчики зарегистрированы")
        
        # Запускаем бота в зависимости от режима
        if WEBHOOK_URL and WEBHOOK_URL.strip():
            # Режим webhook для Railway
            logger.info("🌐 Запуск в режиме webhook...")
            
            # Создаем event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем webhook
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(setup_webhook(application))
            loop.run_until_complete(application.start())
            
            # Запускаем сервер для обработки webhook
            from telegram.ext._utils.webhookhandler import WebhookServer
            
            logger.info(f"🤖 Бот запущен в режиме webhook на порту {PORT}")
            
            # Запускаем сервер
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=WEBHOOK_URL if WEBHOOK_URL.startswith('http') else f'https://{WEBHOOK_URL}',
                drop_pending_updates=True
            )
            
        else:
            # Режим polling для локальной разработки
            logger.warning("⚠️ Запуск в режиме polling (только для разработки!)")
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    # ПРЯМОЙ ЗАПУСК ДЛЯ RAILWAY
    run_bot()
