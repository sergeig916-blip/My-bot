import logging
import time
import urllib.request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ТРЕНИРОВОК ==========
TRAINING_WEEKS = {
    "1": {
        "name": "Неделя 1",
        "days": {
            "1": {
                "name": "Ноги + Грудь",
                "exercises": [
                    "🏋️ Приседания: 50% × 10 × 3 (≈62.5кг)",
                    "🏋️ Жим лежа: 75% × 3 × 5 (≈87.5кг)", 
                    "📊 Разводка гантелей: 17.5кг × 10 × 3",
                    "📊 Обратные сгибания: 25кг × 10 × 4",
                    "💪 Пресс: 3 подхода",
                    "💪 Гиперэкстензия: 20 × 2"
                ]
            },
            "2": {
                "name": "Спина + Плечи", 
                "exercises": [
                    "🏋️ Жим стоя: 35% × 6 × 2 (≈41кг)",
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
                    "🏋️ Жим лежа: 60% × 5 × 2 (≈70кг)",
                    "🏋️ Жим на наклонной: 50% × 6 × 4 (≈58.5кг)",
                    "📊 Разводка на наклонной: 17.5кг × 8 × 4",
                    "📊 Махи в стороны: 4кг × 8 × 4",
                    "📊 Обратный бицепс: 25кг × 8 × 5"
                ]
            }
        }
    },
    "2": {
        "name": "Неделя 2", 
        "days": {
            "1": {
                "name": "Ноги + Грудь",
                "exercises": [
                    "🏋️ Приседания: 55% × 8 × 3 (≈68.5кг)",
                    "🏋️ Жим лежа: 80% × 3 × 4 (≈94кг)",
                    "📊 Разводка гантелей: 17.5кг × 10 × 3",
                    "📊 Обратные сгибания: 25кг × 10 × 4",
                    "💪 Пресс: 3 подхода",
                    "💪 Гиперэкстензия: 20 × 2"
                ]
            },
            "2": {
                "name": "Спина + Плечи",
                "exercises": [
                    "🏋️ Жим стоя: 40% × 6 × 2 (≈47кг)",
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
                    "🏋️ Жим лежа: 65% × 5 × 2 (≈76кг)",
                    "🏋️ Жим на наклонной: 50% × 6 × 4 (≈58.5кг)",
                    "📊 Разводка на наклонной: 17.5кг × 8 × 4",
                    "📊 Махи в стороны: 4кг × 8 × 4",
                    "📊 Обратный бицепс: 25кг × 8 × 5"
                ]
            }
        }
    }
}

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
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
    
    keyboard = [
        [InlineKeyboardButton(f"📋 День 1", callback_data=f"day:{week_num}:1")],
        [InlineKeyboardButton(f"📋 День 2", callback_data=f"day:{week_num}:2")],
        [InlineKeyboardButton(f"📋 День 3", callback_data=f"day:{week_num}:3")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back:start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📅 <b>{TRAINING_WEEKS[week_num]['name']}</b>\n\nВыбери день тренировки:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def show_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировку"""
    query = update.callback_query
    await query.answer()
    
    try:
        _, week_num, day_num = query.data.split(":")
        
        day = TRAINING_WEEKS[week_num]["days"][day_num]
        
        # Формируем текст тренировки
        text = f"<b>📋 {TRAINING_WEEKS[week_num]['name']} • {day['name']}</b>\n\n"
        
        for i, exercise in enumerate(day['exercises'], 1):
            text += f"{i}. {exercise}\n"
        
        text += "\n"
        
        # Клавиатура
        keyboard = [
            [InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_num}:{day_num}")],
            [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"week:{week_num}")],
            [InlineKeyboardButton("🏁 Выбрать неделю", callback_data="back:start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_workout: {e}")
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
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Ошибка. Попробуй /start")
    except:
        pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ТРЕНИРОВОЧНОГО БОТА")
    logger.info("=" * 50)
    
    # АГРЕССИВНЫЙ СБРОС КОНФЛИКТА
    logger.info("🔄 СБРАСЫВАЮ КОНФЛИКТ TELEGRAM...")
    
    try:
        # 1. Сброс вебхука
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",
            timeout=10
        )
        logger.info("✅ Вебхук сброшен")
        time.sleep(5)
        
        # 2. Закрытие соединений
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/close",
            timeout=10
        )
        logger.info("✅ Соединения закрыты")
        time.sleep(10)
        
    except Exception as e:
        logger.warning(f"⚠️ Ошибка сброса: {e}")
    
    # Ждем еще
    logger.info("⏳ Жду 30 секунд перед запуском...")
    time.sleep(30)
    
    logger.info("🎯 Запуск бота...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(show_days, pattern='^week:[12]$'))
        application.add_handler(CallbackQueryHandler(show_workout, pattern='^day:[12]:[123]$'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        application.add_handler(CallbackQueryHandler(handle_back, pattern='^back:'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Все обработчики зарегистрированы")
        logger.info("▶️ Запускаю polling...")
        
        # Запускаем бота
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"💥 ОШИБКА ЗАПУСКА: {e}")
        
        # Если конфликт - ждем и пробуем еще раз
        if "Conflict" in str(e):
            logger.info("⚠️ Конфликт обнаружен. Жду 60 секунд...")
            time.sleep(60)
            logger.info("🔄 Пробую перезапустить...")
            main()  # Рекурсивный перезапуск

if __name__ == '__main__':
    main()
