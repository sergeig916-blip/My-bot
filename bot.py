import os
import logging
import sys
import asyncio
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app/")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ==========
USER_MAXES = {'bench': 117.5, 'squat': 125, 'deadlift': 150}
DEFAULT_ACCESSORY_WEIGHTS = {
    'fly_flat': 17.5, 'fly_incline': 17.5,
    'reverse_curl': 25.0, 'hyperextension_weight': 20.0,
    'horizontal_row': 40.0, 'vertical_pull': 50.0,
    'lateral_raise': 4.0, 'rear_delt_fly': 3.0,
    'leg_extension': 54.0
}

TRAINING_PROGRAM = {
    1: {
        "name": "Неделя 1",
        "day_1": {
            "name": "Ноги + Грудь",
            "code": "Н1Д1",
            "exercises": [
                {"type": "base", "name": "Приседания", "percentage": 50, "reps": 10, "sets": 3},
                {"type": "base", "name": "Жим штанги лежа", "percentage": 75, "reps": 3, "sets": 5},
                {"type": "accessory", "name": "Разводка гантелей лежа", "key": "fly_flat", "reps": 10, "sets": 3},
                {"type": "accessory", "name": "Сгибание рук обратным хватом", "key": "reverse_curl", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "3 подхода", "sets": ""},
                {"type": "accessory", "name": "Гиперэкстензия", "reps": 20, "sets": 2}
            ]
        },
        "day_2": {
            "name": "Спина + Плечи",
            "code": "Н1Д2",
            "exercises": [
                {"type": "base", "name": "Жим штанги стоя", "percentage": 35, "reps": 6, "sets": 2},
                {"type": "accessory", "name": "Гиперэкстензия с весом", "key": "hyperextension_weight", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга вертикального блока", "key": "vertical_pull", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга горизонтального блока", "key": "horizontal_row", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Разводка на заднюю дельту", "key": "rear_delt_fly", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "3 подхода", "sets": ""}
            ]
        },
        "day_3": {
            "name": "Грудь + Плечи",
            "code": "Н1Д3",
            "exercises": [
                {"type": "base", "name": "Жим штанги лежа", "percentage": 60, "reps": 5, "sets": 2},
                {"type": "base", "name": "Жим на наклонной 30°", "percentage": 50, "reps": 6, "sets": 4},
                {"type": "accessory", "name": "Разводка на наклонной", "key": "fly_incline", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Махи гантелей в стороны", "key": "lateral_raise", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Сгибание на бицепс обратным хватом", "key": "reverse_curl", "reps": 8, "sets": 5}
            ]
        }
    },
    2: {
        "name": "Неделя 2",
        "day_1": {
            "name": "Ноги + Грудь",
            "code": "Н2Д1",
            "exercises": [
                {"type": "base", "name": "Приседания", "percentage": 55, "reps": 8, "sets": 3},
                {"type": "base", "name": "Жим штанги лежа", "percentage": 80, "reps": 3, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей лежа", "key": "fly_flat", "reps": 10, "sets": 3},
                {"type": "accessory", "name": "Сгибание рук обратным хватом", "key": "reverse_curl", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "3 подхода", "sets": ""},
                {"type": "accessory", "name": "Гиперэкстензия", "reps": 20, "sets": 2}
            ]
        },
        "day_2": {
            "name": "Спина + Плечи",
            "code": "Н2Д2",
            "exercises": [
                {"type": "base", "name": "Жим штанги стоя", "percentage": 40, "reps": 6, "sets": 2},
                {"type": "accessory", "name": "Гиперэкстензия с весом", "key": "hyperextension_weight", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга вертикального блока", "key": "vertical_pull", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга горизонтального блока", "key": "horizontal_row", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Разводка на заднюю дельту", "key": "rear_delt_fly", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "3 подхода", "sets": ""}
            ]
        },
        "day_3": {
            "name": "Грудь + Плечи",
            "code": "Н2Д3",
            "exercises": [
                {"type": "base", "name": "Жим штанги лежа", "percentage": 65, "reps": 5, "sets": 2},
                {"type": "base", "name": "Жим на наклонной 30°", "percentage": 50, "reps": 6, "sets": 4},
                {"type": "accessory", "name": "Разводка на наклонной", "key": "fly_incline", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Махи гантелей в стороны", "key": "lateral_raise", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Сгибание на бицепс обратным хватом", "key": "reverse_curl", "reps": 8, "sets": 5}
            ]
        }
    }
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def calculate_weight(exercise_name: str, percentage: float):
    exercise_lower = exercise_name.lower()
    
    if "жим" in exercise_lower and "лежа" in exercise_lower:
        base = USER_MAXES['bench']
    elif "присед" in exercise_lower:
        base = USER_MAXES['squat']
    elif "становая" in exercise_lower:
        base = USER_MAXES['deadlift']
    elif "стоя" in exercise_lower:
        base = USER_MAXES['bench'] * 0.6
    else:
        base = USER_MAXES['bench']
    
    weight = base * percentage / 100
    return round(weight / 2.5) * 2.5

def create_progress_bar(completed_days):
    progress = ['⬜', '⬜', '⬜']
    for day_num in completed_days:
        if 1 <= day_num <= 3:
            progress[day_num - 1] = '🟩'
    return ''.join(progress)

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("🏋️ Неделя 1", callback_data="menu:week:1")],
        [InlineKeyboardButton("🏋️ Неделя 2", callback_data="menu:week:2")],
        [InlineKeyboardButton("📊 Мои максимумы", callback_data="menu:maxes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
        "Выбери неделю тренировки:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def show_maxes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать максимумы"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "<b>📊 Твои максимумы:</b>\n\n"
        f"• Жим лежа: {USER_MAXES['bench']}кг\n"
        f"• Присед: {USER_MAXES['squat']}кг\n"
        f"• Становая: {USER_MAXES['deadlift']}кг\n\n"
        "<i>Для изменения максимумов обратитесь к администратору</i>"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_week_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню недели"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu:main":
        keyboard = [
            [InlineKeyboardButton("🏋️ Неделя 1", callback_data="menu:week:1")],
            [InlineKeyboardButton("🏋️ Неделя 2", callback_data="menu:week:2")],
            [InlineKeyboardButton("📊 Мои максимумы", callback_data="menu:maxes")]
        ]
        text = "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\nВыбери неделю тренировки:"
    
    else:
        week_number = int(query.data.split(":")[2])
        completed_days = []  # Пока пусто
        progress_bar = create_progress_bar(completed_days)
        
        keyboard = []
        for day_num in range(1, 4):
            label = f"День {day_num}"
            callback_data = f"day:start:{week_number}:{day_num}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")])
        
        text = f"📅 <b>Неделя {week_number}</b> [{progress_bar}]\n"
        text += f"Завершено: {len(completed_days)}/3 дней\n\n"
        text += "Выбери день:"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def handle_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора дня"""
    query = update.callback_query
    await query.answer()
    
    _, action, week_num_str, day_num_str = query.data.split(":")
    week_number = int(week_num_str)
    day_number = int(day_num_str)
    
    week_data = TRAINING_PROGRAM.get(week_number)
    if not week_data:
        await query.answer("Неделя не найдена")
        return
    
    day_key = f"day_{day_number}"
    if day_key not in week_data:
        await query.answer("День не найден")
        return
    
    day_data = week_data[day_key]
    week_weights = DEFAULT_ACCESSORY_WEIGHTS
    
    # Формируем текст тренировки
    text = f"<b>📋 {day_data['code']} • {day_data['name']}</b>\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(exercise['name'], exercise['percentage'])
            text += f"{i}. <b>{exercise['name']}</b>\n"
            text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        
        elif exercise['type'] == 'accessory':
            text += f"{i}. {exercise['name']}\n"
            if 'key' in exercise:
                weight = week_weights.get(exercise['key'], 0)
                if exercise['reps'] != '3 подхода':
                    text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
                else:
                    text += f"   {exercise['reps']}\n"
            else:
                text += f"   {exercise['reps']}\n"
        
        text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_number}:{day_number}")],
        [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"menu:week:{week_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить тренировку"""
    query = update.callback_query
    await query.answer()
    
    # Просто возвращаемся к меню недели
    await show_week_menu(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуй /start")
    except:
        pass

async def setup_webhook():
    """Настройка webhook для Telegram"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Убедимся, что URL правильный
        webhook_url = WEBHOOK_URL.rstrip('/')
        if not webhook_url.startswith('http'):
            webhook_url = f'https://{webhook_url}'
        
        webhook_url = f"{webhook_url}/{BOT_TOKEN}"
        logger.info(f"🌐 Настройка webhook на: {webhook_url}")
        
        # Ждем чтобы избежать Flood control
        await asyncio.sleep(2)
        
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        logger.info("✅ Webhook установлен")
        
        # Проверяем
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📊 Webhook информация: {webhook_info.url}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке webhook: {e}")
        
        # Если Flood control, ждем и пробуем снова
        if "Flood control" in str(e) or "RetryAfter" in str(e):
            logger.info("⏳ Жду 3 секунды из-за Flood control...")
            await asyncio.sleep(3)
            return await setup_webhook()
        
        return False

def create_application():
    """Создание приложения бота"""
    logger.info("🔧 Создание приложения...")
    
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
    return application

async def main():
    """Основная асинхронная функция"""
    logger.info("🚀 Запуск бота...")
    
    try:
        # Настраиваем webhook
        webhook_set = await setup_webhook()
        
        if not webhook_set:
            logger.error("❌ Не удалось настроить webhook")
            return
        
        # Создаем приложение
        application = create_application()
        
        # Инициализируем приложение (но не запускаем сервер!)
        await application.initialize()
        
        logger.info("🎯 Webhook успешно настроен. Бот готов к работе!")
        logger.info("🤖 Бот готов принимать обновления через webhook")
        
        # Просто ждем - Railway сам обрабатывает HTTP запросы
        # Бот будет получать обновления через webhook
        while True:
            await asyncio.sleep(3600)  # Спим 1 час
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

def run_bot():
    """Точка входа для Railway"""
    logger.info("🚀 Запуск бота на Railway...")
    
    # Запускаем асинхронную функцию
    asyncio.run(main())

if __name__ == '__main__':
    run_bot()
