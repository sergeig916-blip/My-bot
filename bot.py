import logging
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПРОСТЫЕ ДАННЫЕ ==========
TRAINING_WEEKS = {
    "week_1": {
        "name": "Неделя 1",
        "days": {
            "1": {
                "name": "Ноги + Грудь",
                "exercises": [
                    "🏋️ Приседания: 50% × 10 × 3",
                    "🏋️ Жим лежа: 75% × 3 × 5", 
                    "📊 Разводка гантелей: 17.5кг × 10 × 3",
                    "📊 Обратные сгибания: 25кг × 10 × 4",
                    "💪 Пресс: 3 подхода",
                    "💪 Гиперэкстензия: 20 × 2"
                ]
            },
            "2": {
                "name": "Спина + Плечи", 
                "exercises": [
                    "🏋️ Жим стоя: 35% × 6 × 2",
                    "📊 Гиперэкстензия с весом: 20кг × 10 × 4",
                    "📊 Тяга вертикальная: 50кг × 10 × 4",
                    "📊 Тяга горизонтальная: 40кг × 10 × 4",
                    "📊 Задняя дельта: 3кг × 10 × 4",
                    "💪 Пресс: 3 подхода"
                ]
            },
            "3": {
                "name": "Грудь + Плечи",
                "exercises": [
                    "🏋️ Жим лежа: 60% × 5 × 2",
                    "🏋️ Жим на наклонной: 50% × 6 × 4",
                    "📊 Разводка на наклонной: 17.5кг × 8 × 4",
                    "📊 Махи в стороны: 4кг × 8 × 4",
                    "📊 Обратный бицепс: 25кг × 8 × 5"
                ]
            }
        }
    },
    "week_2": {
        "name": "Неделя 2", 
        "days": {
            "1": {
                "name": "Ноги + Грудь",
                "exercises": [
                    "🏋️ Приседания: 55% × 8 × 3",
                    "🏋️ Жим лежа: 80% × 3 × 4",
                    "📊 Разводка гантелей: 17.5кг × 10 × 3",
                    "📊 Обратные сгибания: 25кг × 10 × 4",
                    "💪 Пресс: 3 подхода",
                    "💪 Гиперэкстензия: 20 × 2"
                ]
            },
            "2": {
                "name": "Спина + Плечи",
                "exercises": [
                    "🏋️ Жим стоя: 40% × 6 × 2",
                    "📊 Гиперэкстензия с весом: 20кг × 10 × 4",
                    "📊 Тяга вертикальная: 50кг × 10 × 4",
                    "📊 Тяга горизонтальная: 40кг × 10 × 4",
                    "📊 Задняя дельта: 3кг × 10 × 4",
                    "💪 Пресс: 3 подхода"
                ]
            },
            "3": {
                "name": "Грудь + Плечи",
                "exercises": [
                    "🏋️ Жим лежа: 65% × 5 × 2",
                    "🏋️ Жим на наклонной: 50% × 6 × 4",
                    "📊 Разводка на наклонной: 17.5кг × 8 × 4",
                    "📊 Махи в стороны: 4кг × 8 × 4",
                    "📊 Обратный бицепс: 25кг × 8 × 5"
                ]
            }
        }
    }
}

# ========== СБРОС КОНФЛИКТА ==========
def reset_telegram_conflict():
    """Агрессивный сброс конфликта в Telegram"""
    logger.info("🔄 Сбрасываю конфликт Telegram...")
    
    try:
        # 1. Удаляем вебхук
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
        time.sleep(2)
        
        # 2. Закрываем все соединения
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/close", timeout=10)
        time.sleep(2)
        
        # 3. Проверяем бота
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram API сброшен успешно")
            return True
        else:
            logger.error("❌ Не удалось сбросить Telegram API")
            return False
            
    except Exception as e:
        logger.error(f"⚠️ Ошибка сброса: {e}")
        return False

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("📅 Неделя 1", callback_data="week:1")],
        [InlineKeyboardButton("📅 Неделя 2", callback_data="week:2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
        "Твои максималы:\n"
        "• Жим лежа: 117.5кг\n"
        "• Присед: 125кг\n"
        "• Становая: 150кг\n\n"
        "Выбери неделю:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def show_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать дни недели"""
    query = update.callback_query
    await query.answer()
    
    week_num = query.data.split(":")[1]
    week_key = f"week_{week_num}"
    
    keyboard = [
        [InlineKeyboardButton(f"📋 День 1", callback_data=f"day:{week_num}:1")],
        [InlineKeyboardButton(f"📋 День 2", callback_data=f"day:{week_num}:2")],
        [InlineKeyboardButton(f"📋 День 3", callback_data=f"day:{week_num}:3")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back:start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📅 <b>{TRAINING_WEEKS[week_key]['name']}</b>\n\nВыбери день тренировки:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def show_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировку"""
    query = update.callback_query
    await query.answer()
    
    try:
        _, week_num, day_num = query.data.split(":")
        week_key = f"week_{week_num}"
        
        day = TRAINING_WEEKS[week_key]["days"][day_num]
        
        # Формируем текст
        text = f"<b>📋 {TRAINING_WEEKS[week_key]['name']} • {day['name']}</b>\n\n"
        
        for i, exercise in enumerate(day['exercises'], 1):
            text += f"{i}. {exercise}\n"
        
        text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("✅ Завершить", callback_data=f"complete:{week_num}:{day_num}")],
            [InlineKeyboardButton("⬅️ К дням", callback_data=f"week:{week_num}")],
            [InlineKeyboardButton("🏁 На главную", callback_data="back:start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await query.edit_message_text("❌ Ошибка загрузки тренировки")

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить тренировку"""
    query = update.callback_query
    await query.answer("✅ Тренировка завершена!")
    
    await query.edit_message_text(
        "🎉 <b>Тренировка завершена!</b>\n\n"
        "Отличная работа! 💪\n\n"
        "Нажми /start чтобы продолжить",
        parse_mode='HTML'
    )

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка Назад"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back:start":
        keyboard = [
            [InlineKeyboardButton("📅 Неделя 1", callback_data="week:1")],
            [InlineKeyboardButton("📅 Неделя 2", callback_data="week:2")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\nВыбери неделю:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.callback_query:
        try:
            await update.callback_query.answer("⚠️ Ошибка, попробуйте /start")
        except:
            pass

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ТРЕНИРОВОЧНОГО БОТА")
    logger.info("=" * 50)
    
    # 1. Агрессивный сброс конфликта
    logger.info("🔄 Этап 1: Сброс конфликта Telegram...")
    if not reset_telegram_conflict():
        logger.warning("⚠️ Не удалось сбросить конфликт, продолжаем...")
    
    # 2. Ждем
    logger.info("⏳ Этап 2: Жду 15 секунд...")
    time.sleep(15)
    
    # 3. Запускаем бота
    logger.info("🎯 Этап 3: Запуск бота...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(show_days, pattern=r'^week:[12]$'))
        application.add_handler(CallbackQueryHandler(show_workout, pattern=r'^day:[12]:[123]$'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern=r'^complete:'))
        application.add_handler(CallbackQueryHandler(handle_back, pattern=r'^back:'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Все обработчики зарегистрированы")
        logger.info("▶️ Запускаю polling...")
        
        # Запуск с увеличенными таймаутами
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=60,
            read_latency=10.0,
            connect_timeout=30.0,
            pool_timeout=30.0
        )
        
    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.info("🔄 Перезапуск через 30 секунд...")
        time.sleep(30)
        main()  # Рекурсивный перезапуск

if __name__ == '__main__':
    main()
