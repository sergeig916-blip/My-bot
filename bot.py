import logging
import time
import asyncio
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import Conflict

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ГЛОБАЛЬНЫЕ ДАННЫЕ ==========
USER_MAXES = {'bench': 117.5, 'squat': 125, 'deadlift': 150}

# Исходные веса подсобки (кг)
DEFAULT_ACCESSORY_WEIGHTS = {
    'fly_flat': 17.5,
    'fly_incline': 17.5,
    'reverse_curl': 25.0,
    'hyperextension_weight': 20.0,
    'horizontal_row': 40.0,
    'vertical_pull': 50.0,
    'lateral_raise': 4.0,
    'rear_delt_fly': 3.0,
    'leg_extension': 54.0
}

# Структура программы тренировок
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
    for day in completed_days:
        day_num = int(day.split('_')[1]) - 1
        if 0 <= day_num < 3:
            progress[day_num] = '🟩'
    return ''.join(progress)

def get_unique_accessory_exercises(week_data):
    exercises = []
    seen_keys = set()
    
    for day_key in ['day_1', 'day_2', 'day_3']:
        if day_key in week_data:
            for exercise in week_data[day_key]['exercises']:
                if exercise['type'] == 'accessory' and 'key' in exercise:
                    key = exercise['key']
                    if key not in seen_keys:
                        seen_keys.add(key)
                        exercises.append({
                            'key': key,
                            'name': exercise['name']
                        })
    
    return exercises

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    query = update.callback_query
    await query.answer()
    
    text = (
        "<b>📊 Твои максимумы:</b>\n\n"
        f"• Жим лежа: {USER_MAXES['bench']}кг\n"
        f"• Присед: {USER_MAXES['squat']}кг\n"
        f"• Становая: {USER_MAXES['deadlift']}кг\n\n"
        "<i>Для изменения максимумов обратитесь к администратору</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_week_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        week_num = query.data.split(":")[2]
        week_key = f"week_{week_num}"
        week_data = TRAINING_PROGRAM[week_key]
        
        completed_days = week_data.get('completed_days', [])
        progress_bar = create_progress_bar(completed_days)
        
        keyboard = []
        for day_num in range(1, 4):
            day_key = f"day_{day_num}"
            
            if day_key in completed_days:
                label = f"✅ День {day_num}"
                callback_data = f"day:view:{week_num}:{day_num}"
            else:
                label = f"День {day_num}"
                callback_data = f"day:start:{week_num}:{day_num}"
            
            keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")])
        
        text = f"📅 <b>Неделя {week_num}</b> [{progress_bar}]\n"
        text += f"Завершено: {len(completed_days)}/3 дней\n\n"
        text += "Выбери день:"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def handle_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, action, week_num, day_num = query.data.split(":")
    week_key = f"week_{week_num}"
    day_key = f"day_{day_num}"
    
    context.user_data['current_week'] = week_key
    context.user_data['current_day'] = day_key
    context.user_data['week_num'] = week_num
    context.user_data['day_num'] = day_num
    
    week_data = TRAINING_PROGRAM[week_key]
    
    if action == 'view' or day_key in week_data.get('completed_days', []):
        await show_completed_day(update, context, week_key, day_key)
        return
    
    if not week_data.get('weights_set', False):
        await ask_about_weights(update, context, week_key, day_key)
    else:
        await show_workout(update, context, week_key, day_key)

async def ask_about_weights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    week_key = context.user_data['current_week']
    week_data = TRAINING_PROGRAM[week_key]
    week_num = week_data['number']
    
    accessory_exercises = get_unique_accessory_exercises(week_data)
    week_weights = week_data['week_weights']
    
    weights_text = f"<b>🏋️ Веса подсобки для недели {week_num}:</b>\n\n"
    
    for i, exercise in enumerate(accessory_exercises, 1):
        weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
        weights_text += f"{i}. {exercise['name']}: {weight}кг\n"
    
    context.user_data['accessory_exercises'] = accessory_exercises
    context.user_data['edit_index'] = 0
    
    keyboard = [
        [InlineKeyboardButton("✅ Оставить эти веса", callback_data="weights:keep")],
        [InlineKeyboardButton("✏️ Изменить веса", callback_data="weights:edit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        weights_text + "\nИспользовать эти веса для всей недели?",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_weights_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    decision = query.data.split(":")[1]
    
    if decision == 'keep':
        week_key = context.user_data['current_week']
        TRAINING_PROGRAM[week_key]['weights_set'] = True
        await show_workout(update, context, week_key, context.user_data['current_day'])
    
    elif decision == 'edit':
        await edit_weight(update, context, 0)

async def edit_weight(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    query = update.callback_query
    await query.answer()
    
    accessory_exercises = context.user_data.get('accessory_exercises', [])
    
    if index >= len(accessory_exercises):
        week_key = context.user_data['current_week']
        TRAINING_PROGRAM[week_key]['weights_set'] = True
        await show_workout(update, context, week_key, context.user_data['current_day'])
        return
    
    exercise = accessory_exercises[index]
    week_key = context.user_data['current_week']
    current_weight = TRAINING_PROGRAM[week_key]['week_weights'].get(
        exercise['key'], 
        DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0)
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖2.5кг", callback_data=f"weight:change:{index}:-2.5"),
            InlineKeyboardButton("➖5кг", callback_data=f"weight:change:{index}:-5"),
            InlineKeyboardButton("➖7.5кг", callback_data=f"weight:change:{index}:-7.5")
        ],
        [
            InlineKeyboardButton(f"✅ {current_weight}кг", callback_data=f"weight:skip:{index}")
        ],
        [
            InlineKeyboardButton("➕2.5кг", callback_data=f"weight:change:{index}:2.5"),
            InlineKeyboardButton("➕5кг", callback_data=f"weight:change:{index}:5"),
            InlineKeyboardButton("➕7.5кг", callback_data=f"weight:change:{index}:7.5")
        ],
        [InlineKeyboardButton("⏭ Пропустить", callback_data=f"weight:skip:{index}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"<b>Редактирование веса ({index + 1}/{len(accessory_exercises)})</b>\n\n"
        f"Упражнение: {exercise['name']}\n"
        f"Текущий вес: {current_weight}кг\n\n"
        f"Выбери изменение:"
    )
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def handle_weight_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, _, index, change = query.data.split(":")
    change = float(change)
    
    accessory_exercises = context.user_data.get('accessory_exercises', [])
    if index.isdigit():
        index = int(index)
    
    if 0 <= index < len(accessory_exercises):
        exercise = accessory_exercises[index]
        week_key = context.user_data['current_week']
        
        current_weight = TRAINING_PROGRAM[week_key]['week_weights'].get(
            exercise['key'], 
            DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0)
        )
        new_weight = max(0, current_weight + change)
        
        TRAINING_PROGRAM[week_key]['week_weights'][exercise['key']] = new_weight
        
        context.user_data['edit_index'] = index + 1
        await edit_weight(update, context, index + 1)

async def handle_weight_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.split(":")[2])
    context.user_data['edit_index'] = index + 1
    await edit_weight(update, context, index + 1)

async def show_workout(update: Update, context: ContextTypes.DEFAULT_TYPE, week_key: str, day_key: str):
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    week_data = TRAINING_PROGRAM[week_key]
    day_data = week_data[day_key]
    week_weights = week_data['week_weights']
    
    text = f"<b>📋 {day_data['code']} • {day_data['name']}</b>\n\n"
    
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
    
    week_num = week_data['number']
    day_num = int(day_key.split('_')[1])
    
    keyboard = [
        [InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_num}:{day_num}")],
        [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"menu:week:{week_num}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_completed_day(update: Update, context: ContextTypes.DEFAULT_TYPE, week_key: str, day_key: str):
    query = update.callback_query
    await query.answer()
    
    week_data = TRAINING_PROGRAM[week_key]
    day_data = week_data[day_key]
    week_weights = week_data['week_weights']
    
    text = f"<b>✅ {day_data['code']} (завершено)</b>\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(exercise['name'], exercise['percentage'])
            text += f"{i}. <b>{exercise['name']}</b>\n"
            text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        elif exercise['type'] == 'accessory' and 'key' in exercise:
            weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
            text += f"{i}. {exercise['name']}\n"
            if exercise['reps'] != '3 подхода':
                text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        
        text += "\n"
    
    week_num = week_data['number']
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"menu:week:{week_num}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    week_num = int(query.data.split(":")[1])
    day_num = int(query.data.split(":")[2])
    
    week_key = f"week_{week_num}"
    day_key = f"day_{day_num}"
    
    if week_key in TRAINING_PROGRAM:
        if 'completed_days' not in TRAINING_PROGRAM[week_key]:
            TRAINING_PROGRAM[week_key]['completed_days'] = []
        
        if day_key not in TRAINING_PROGRAM[week_key]['completed_days']:
            TRAINING_PROGRAM[week_key]['completed_days'].append(day_key)
    
    await show_week_menu(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуй /start")
    except:
        pass

class BotManager:
    def __init__(self):
        self.application = None
        self.running = False
        self.stop_event = asyncio.Event()
        
    async def create_application(self):
        """Создать новое приложение бота"""
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        self.application.add_handler(CommandHandler('start', start))
        self.application.add_handler(CallbackQueryHandler(show_maxes, pattern='^menu:maxes$'))
        self.application.add_handler(CallbackQueryHandler(show_week_menu, pattern='^menu:'))
        self.application.add_handler(CallbackQueryHandler(handle_day_selection, pattern='^day:'))
        self.application.add_handler(CallbackQueryHandler(handle_weights_decision, pattern='^weights:(keep|edit)$'))
        self.application.add_handler(CallbackQueryHandler(handle_weight_change, pattern='^weight:change:'))
        self.application.add_handler(CallbackQueryHandler(handle_weight_skip, pattern='^weight:skip:'))
        self.application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        self.application.add_error_handler(error_handler)
        
        return self.application
    
    async def run_bot(self):
        """Запустить бота с обработкой конфликтов"""
        retry_count = 0
        max_retries = 10
        
        while not self.stop_event.is_set() and retry_count < max_retries:
            try:
                logger.info(f"🔄 Попытка запуска бота #{retry_count + 1}...")
                
                # Создаем новое приложение
                app = await self.create_application()
                
                # Инициализируем и запускаем
                await app.initialize()
                await app.start()
                
                # Запускаем polling с параметрами
                await app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES,
                    timeout=10,
                    poll_interval=0.5
                )
                
                logger.info("🤖 Бот успешно запущен и работает")
                self.running = True
                
                # Ждем либо остановки, либо ошибки
                try:
                    while not self.stop_event.is_set():
                        await asyncio.sleep(1)
                        
                        # Проверяем, жив ли апдейтер
                        if not app.updater.running:
                            logger.warning("⚠️ Updater остановлен, перезапускаем...")
                            break
                            
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"⚠️ Ошибка в основном цикле: {e}")
                    break
                    
                finally:
                    # Останавливаем приложение
                    self.running = False
                    try:
                        await app.updater.stop()
                        await app.stop()
                        await app.shutdown()
                    except:
                        pass
                    
            except Conflict as e:
                logger.warning(f"⚠️ Конфликт обнаружен (попытка {retry_count + 1}): {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_time = 5 * 60  # 5 минут
                    logger.info(f"⏳ Жду {wait_time/60} минут перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("💥 Достигнут лимит попыток перезапуска")
                    break
                    
            except Exception as e:
                logger.error(f"💥 Критическая ошибка: {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_time = 60  # 1 минута
                    logger.info(f"⏳ Жду {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("💥 Достигнут лимит попыток перезапуска")
                    break
    
    async def stop(self):
        """Остановить бота"""
        self.stop_event.set()
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except:
                pass

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск менеджера бота...")
    
    # Создаем менеджер
    manager = BotManager()
    
    # Обработчик сигналов для корректного завершения
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(manager.stop()))
    
    try:
        # Запускаем бота
        await manager.run_bot()
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал прерывания")
    finally:
        logger.info("👋 Завершение работы бота")
        await manager.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Программа завершена")
