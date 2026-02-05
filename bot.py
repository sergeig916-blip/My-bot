import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ТРЕНИРОВОК ==========
USER_MAXES = {'bench': 117.5, 'squat': 125, 'deadlift': 150}

DEFAULT_ACCESSORY_WEIGHTS = {
    'fly_flat': 17.5, 'fly_incline': 17.5,
    'reverse_curl': 25.0, 'hyperextension_weight': 20.0,
    'horizontal_row': 40.0, 'vertical_pull': 50.0,
    'lateral_raise': 4.0, 'rear_delt_fly': 3.0,
    'leg_extension': 54.0
}

TRAINING_PROGRAM = {
    "week_1": {
        "number": 1,
        "completed_days": [],
        "weights_set": False,
        "week_weights": DEFAULT_ACCESSORY_WEIGHTS.copy(),
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
    "week_2": {
        "number": 2,
        "completed_days": [],
        "weights_set": False,
        "week_weights": DEFAULT_ACCESSORY_WEIGHTS.copy(),
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
def calculate_weight(exercise_name, percentage):
    """Расчет веса для базового упражнения"""
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
    """Создание прогресс-бара"""
    progress = ['⬜', '⬜', '⬜']
    for day in completed_days:
        day_num = int(day.split('_')[1]) - 1
        if 0 <= day_num < 3:
            progress[day_num] = '🟩'
    return ''.join(progress)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = []
    
    for week_key, week_data in sorted(TRAINING_PROGRAM.items(), key=lambda x: x[1]['number']):
        week_num = week_data['number']
        completed_days = week_data.get('completed_days', [])
        progress_bar = create_progress_bar(completed_days)
        
        if len(completed_days) == 3:
            label = f"✅ Неделя {week_num} [{progress_bar}]"
        else:
            label = f"Неделя {week_num} [{progress_bar}]"
        
        keyboard.append([InlineKeyboardButton(label, callback_data=f"week:{week_num}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
        "Твои максималы:\n"
        f"• Жим лежа: {USER_MAXES['bench']}кг\n"
        f"• Присед: {USER_MAXES['squat']}кг\n"
        f"• Становая: {USER_MAXES['deadlift']}кг\n\n"
        "Выбери неделю:"
    )
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_days_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню дней недели"""
    query = update.callback_query
    await query.answer()
    
    try:
        week_num = int(query.data.split(':')[1])
        week_key = f"week_{week_num}"
        week_data = TRAINING_PROGRAM[week_key]
        
        completed_days = week_data.get('completed_days', [])
        progress_bar = create_progress_bar(completed_days)
        
        keyboard = []
        for day_num in range(1, 4):
            day_key = f"day_{day_num}"
            
            if day_key in completed_days:
                label = f"✅ День {day_num}"
                callback_data = f"view:{week_num}:{day_num}"
            else:
                label = f"День {day_num}"
                callback_data = f"day:{week_num}:{day_num}"
            
            keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к неделям", callback_data="back:weeks")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"📅 <b>Неделя {week_num}</b> [{progress_bar}]\n"
        text += f"Завершено: {len(completed_days)}/3 дней\n\n"
        text += "Выбери день тренировки:"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Ошибка в show_days_menu: {e}")
        await query.edit_message_text("❌ Ошибка. Нажми /start")

async def show_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировку"""
    query = update.callback_query
    await query.answer()
    
    try:
        data_parts = query.data.split(':')
        action = data_parts[0]  # day или view
        week_num = int(data_parts[1])
        day_num = int(data_parts[2])
        
        week_key = f"week_{week_num}"
        day_key = f"day_{day_num}"
        
        if week_key not in TRAINING_PROGRAM or day_key not in TRAINING_PROGRAM[week_key]:
            await query.edit_message_text("❌ Тренировка не найдена")
            return
        
        week_data = TRAINING_PROGRAM[week_key]
        day_data = week_data[day_key]
        week_weights = week_data['week_weights']
        
        # Формируем текст тренировки
        text = f"📋 <b>{day_data['code']} • {day_data['name']}</b>\n\n"
        
        for i, exercise in enumerate(day_data['exercises'], 1):
            if exercise['type'] == 'base':
                weight = calculate_weight(exercise['name'], exercise['percentage'])
                text += f"{i}. <b>{exercise['name']}</b>\n"
                text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
            
            elif exercise['type'] == 'accessory':
                text += f"{i}. {exercise['name']}\n"
                if 'key' in exercise:
                    weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
                    if exercise['reps'] != '3 подхода':
                        text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
                    else:
                        text += f"   {exercise['reps']}\n"
                else:
                    text += f"   {exercise['reps']}\n"
            
            text += "\n"
        
        # Клавиатура
        keyboard = []
        
        if action == 'day':  # Только для активных тренировок
            keyboard.append([InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_num}:{day_num}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ К дням недели", callback_data=f"week:{week_num}")])
        keyboard.append([InlineKeyboardButton("🏁 Выбрать неделю", callback_data="back:weeks")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Ошибка в show_workout: {e}")
        await query.edit_message_text("❌ Ошибка загрузки тренировки")

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить тренировку как завершенную"""
    query = update.callback_query
    await query.answer()
    
    try:
        data_parts = query.data.split(':')
        week_num = int(data_parts[1])
        day_num = int(data_parts[2])
        
        week_key = f"week_{week_num}"
        day_key = f"day_{day_num}"
        
        if week_key in TRAINING_PROGRAM:
            if 'completed_days' not in TRAINING_PROGRAM[week_key]:
                TRAINING_PROGRAM[week_key]['completed_days'] = []
            
            if day_key not in TRAINING_PROGRAM[week_key]['completed_days']:
                TRAINING_PROGRAM[week_key]['completed_days'].append(day_key)
        
        await query.edit_message_text("✅ Тренировка отмечена как завершенная! 🎉\n\nНажми /start для продолжения")
    
    except Exception as e:
        logger.error(f"Ошибка в complete_workout: {e}")
        await query.edit_message_text("❌ Ошибка")

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки Назад"""
    query = update.callback_query
    await query.answer()
    
    await start(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Ошибка. Попробуй еще раз")
    except:
        pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска бота"""
    logger.info("⏳ Жду 10 секунд перед запуском...")
    time.sleep(10)  # Ждем чтобы Telegram успокоился
    
    logger.info("🚀 Бот запускается...")
    logger.info(f"✅ Токен: {BOT_TOKEN[:10]}...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(show_days_menu, pattern=r'^week:\d+$'))
        application.add_handler(CallbackQueryHandler(show_workout, pattern=r'^(day|view):\d+:\d+$'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern=r'^complete:\d+:\d+$'))
        application.add_handler(CallbackQueryHandler(handle_back, pattern=r'^back:'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Все обработчики зарегистрированы")
        
        # Запускаем бота с обработкой конфликтов
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Попытка запуска #{attempt + 1}")
                
                application.run_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES,
                    timeout=30,
                    read_latency=5.0
                )
                break
                
            except Exception as e:
                if "Conflict" in str(e) and attempt < max_retries - 1:
                    wait_time = 20 * (attempt + 1)
                    logger.warning(f"⚠️ Конфликт. Жду {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    raise
        
        logger.info("✅ Бот успешно остановлен")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
