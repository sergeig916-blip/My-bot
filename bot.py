import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# В Railway используем переменные окружения, а не .env
# Удаляем: from dotenv import load_dotenv
# Удаляем: load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

USER_MAXES = {'bench': 117.5, 'squat': 125, 'deadlift': 150}

DEFAULT_ACCESSORY_WEIGHTS = {
    'fly_flat': 17.5, 'fly_incline': 17.5,
    'reverse_curl': 25.0, 'hyperextension_weight': 20.0,
    'horizontal_row': 40.0, 'vertical_pull': 50.0,
    'lateral_raise': 4.0, 'rear_delt_fly': 3.0,
    'leg_extension': 54.0
}

# Полная программа тренировок (неделя 1)
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
                {"type": "base", "name": "Приседания", "percentage": 50, "reps": 10, "sets": 3, "alternative": True},
                {"type": "base", "name": "Жим штанги лежа", "percentage": 75, "reps": 3, "sets": 5},
                {"type": "accessory", "name": "Разводка гантелей лежа на скамье", "key": "fly_flat", "reps": 10, "sets": 3},
                {"type": "accessory", "name": "Сгибание рук со штангой обратным хватом", "key": "reverse_curl", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "-", "sets": "-"},
                {"type": "accessory", "name": "Гиперэкстензия", "reps": 20, "sets": 2}
            ]
        },
        "day_2": {
            "name": "Спина + Плечи",
            "code": "Н1Д2",
            "exercises": [
                {"type": "base", "name": "Жим штанги стоя", "percentage": 35, "reps": 6, "sets": 2},
                {"type": "accessory", "name": "Гиперэкстензия с весом", "key": "hyperextension_weight", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга вертикального блока широким хватом", "key": "vertical_pull", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Горизонтальная тяга блока к поясу", "key": "horizontal_row", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей сидя (задняя дельта)", "key": "rear_delt_fly", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "-", "sets": "-"}
            ]
        },
        "day_3": {
            "name": "Грудь + Плечи",
            "code": "Н1Д3",
            "exercises": [
                {"type": "base", "name": "Жим штанги лежа", "percentage": 60, "reps": 5, "sets": 2},
                {"type": "base", "name": "Жим штанги лежа на скамье 30°", "percentage": 50, "reps": 6, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей лежа на скамье 30°", "key": "fly_incline", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Махи гантелей в сторону", "key": "lateral_raise", "reps": 8, "sets": 4},
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
                {"type": "base", "name": "Приседания", "percentage": 55, "reps": 8, "sets": 3, "alternative": True},
                {"type": "base", "name": "Жим штанги лежа", "percentage": 80, "reps": 3, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей лежа на скамье", "key": "fly_flat", "reps": 10, "sets": 3},
                {"type": "accessory", "name": "Сгибание рук со штангой обратным хватом", "key": "reverse_curl", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "-", "sets": "-"},
                {"type": "accessory", "name": "Гиперэкстензия", "reps": 20, "sets": 2}
            ]
        },
        "day_2": {
            "name": "Спина + Плечи",
            "code": "Н2Д2",
            "exercises": [
                {"type": "base", "name": "Жим штанги стоя", "percentage": 40, "reps": 6, "sets": 2},
                {"type": "accessory", "name": "Гиперэкстензия с весом", "key": "hyperextension_weight", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Тяга вертикального блока широким хватом", "key": "vertical_pull", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Горизонтальная тяга блока к поясу", "key": "horizontal_row", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей сидя (задняя дельта)", "key": "rear_delt_fly", "reps": 10, "sets": 4},
                {"type": "accessory", "name": "Пресс", "reps": "-", "sets": "-"}
            ]
        },
        "day_3": {
            "name": "Грудь + Плечи",
            "code": "Н2Д3",
            "exercises": [
                {"type": "base", "name": "Жим штанги лежа", "percentage": 65, "reps": 5, "sets": 2},
                {"type": "base", "name": "Жим штанги лежа на скамье 30°", "percentage": 50, "reps": 6, "sets": 4},
                {"type": "accessory", "name": "Разводка гантелей лежа на скамье 30°", "key": "fly_incline", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Махи гантелей в сторону", "key": "lateral_raise", "reps": 8, "sets": 4},
                {"type": "accessory", "name": "Сгибание на бицепс обратным хватом", "key": "reverse_curl", "reps": 8, "sets": 5}
            ]
        }
    }
}

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

def get_week_accessory_exercises(week_data):
    """Получить ВСЕ аксессуарные упражнения недели с сохранением порядка"""
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
                            'name': exercise['name'],
                            'day': day_key
                        })
    
    return exercises

async def start(update: Update, context: CallbackContext):
    """Начало работы с ботом - показываем список недель"""
    await show_weeks_menu(update, context)

async def show_weeks_menu(update: Update, context: CallbackContext):
    """Показать меню выбора недели"""
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
    
    text = "🏋️ Бот программы 'Жим 150'\n\nВыбери неделю тренировки:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_days_menu(update: Update, context: CallbackContext, week_num: int):
    """Показать меню дней недели"""
    query = update.callback_query
    await query.answer()
    
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
            callback_data = f"start:{week_num}:{day_num}"
        
        keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("← Назад к неделям", callback_data="menu:weeks")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"Неделя {week_num} [{progress_bar}]\n"
    text += f"Завершено: {len(completed_days)}/3\n\n"
    text += "Выбери день:"
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_day_selection(update: Update, context: CallbackContext):
    """Обработка выбора дня"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(':')
    action = data_parts[0]  # start или view
    week_num = int(data_parts[1])
    day_num = int(data_parts[2])
    
    week_key = f"week_{week_num}"
    day_key = f"day_{day_num}"
    
    # Сохраняем в контексте
    context.user_data['current_week'] = week_key
    context.user_data['current_day'] = day_key
    context.user_data['week_num'] = week_num
    context.user_data['day_num'] = day_num
    
    week_data = TRAINING_PROGRAM[week_key]
    
    # Если день уже завершен, показываем его
    if action == 'view' or day_key in week_data.get('completed_days', []):
        await show_completed_day(update, context, week_key, day_key)
        return
    
    # Проверяем, установлены ли веса для недели
    if not week_data.get('weights_set', False):
        await ask_about_weights(update, context, week_key, day_key)
    else:
        await show_workout(update, context, week_key, day_key)

async def ask_about_weights(update: Update, context: CallbackContext, week_key: str, day_key: str):
    """Спросить про использование текущих весов"""
    query = update.callback_query
    await query.answer()
    
    week_data = TRAINING_PROGRAM[week_key]
    week_num = week_data['number']
    
    # Получаем ВСЕ упражнения недели
    accessory_exercises = get_week_accessory_exercises(week_data)
    week_weights = week_data['week_weights']
    
    # Формируем текст с весами
    weights_text = "<b>Веса для этой недели:</b>\n\n"
    
    for i, exercise in enumerate(accessory_exercises, 1):
        weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
        weights_text += f"{i}. {exercise['name']}: {weight}кг\n"
    
    # Сохраняем упражнения в контексте для редактирования
    context.user_data['week_exercises'] = accessory_exercises
    context.user_data['weights_to_edit'] = [
        {
            'key': ex['key'],
            'name': ex['name'],
            'current_weight': week_weights.get(ex['key'], DEFAULT_ACCESSORY_WEIGHTS.get(ex['key'], 0))
        }
        for ex in accessory_exercises
    ]
    context.user_data['edit_index'] = 0
    
    keyboard = [
        [InlineKeyboardButton("✅ Использовать эти веса", callback_data="weights:use_current")],
        [InlineKeyboardButton("✏️ Изменить веса", callback_data="weights:edit")],
        [InlineKeyboardButton("← Назад к дням", callback_data=f"menu:days:{week_num}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{weights_text}\nИспользовать эти веса для всей недели?",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_weights_decision(update: Update, context: CallbackContext):
    """Обработка решения по весам"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(':')
    decision = data_parts[1]  # use_current или edit
    
    week_key = context.user_data.get('current_week')
    day_key = context.user_data.get('current_day')
    week_num = context.user_data.get('week_num')
    
    if decision == 'use_current':
        # Устанавливаем флаг, что веса установлены
        TRAINING_PROGRAM[week_key]['weights_set'] = True
        await show_workout(update, context, week_key, day_key)
    
    elif decision == 'edit':
        await show_edit_weight(update, context, 0)

async def show_edit_weight(update: Update, context: CallbackContext, index: int):
    """Показать упражнение для редактирования веса"""
    query = update.callback_query
    await query.answer()
    
    weights_to_edit = context.user_data.get('weights_to_edit', [])
    
    if index >= len(weights_to_edit):
        # Все упражнения отредактированы
        week_key = context.user_data.get('current_week')
        day_key = context.user_data.get('current_day')
        
        # Устанавливаем флаг, что веса установлены
        TRAINING_PROGRAM[week_key]['weights_set'] = True
        
        # Обновляем веса в программе
        week_weights = TRAINING_PROGRAM[week_key]['week_weights']
        for weight_data in weights_to_edit:
            week_weights[weight_data['key']] = weight_data['current_weight']
        
        await show_workout(update, context, week_key, day_key)
        return
    
    exercise = weights_to_edit[index]
    current_weight = exercise['current_weight']
    
    # Создаем клавиатуру для выбора веса
    keyboard = []
    
    # Кнопки изменения веса
    changes = [-5, -2.5, 0, 2.5, 5]
    row = []
    
    for change in changes:
        new_weight = max(0, round(current_weight + change, 1))
        if change == 0:
            label = f"✅ {new_weight}"
        elif change < 0:
            label = f"🔽 {new_weight}"
        else:
            label = f"🔼 {new_weight}"
        
        row.append(InlineKeyboardButton(label, callback_data=f"weight:set:{index}:{new_weight}"))
    
    keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Ввести другой вес", callback_data=f"weight:custom:{index}")])
    keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data=f"weight:skip:{index}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"<b>Редактирование весов ({index + 1}/{len(weights_to_edit)})</b>\n\n"
    text += f"Упражнение: {exercise['name']}\n"
    text += f"Текущий вес: {current_weight}кг\n\n"
    text += "Выбери новый вес:"
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def handle_weight_edit(update: Update, context: CallbackContext):
    """Обработка редактирования веса"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(':')
    action = data_parts[1]  # set, custom, skip
    index = int(data_parts[2])
    
    weights_to_edit = context.user_data.get('weights_to_edit', [])
    
    if action == 'set':
        new_weight = float(data_parts[3])
        weights_to_edit[index]['current_weight'] = new_weight
        context.user_data['edit_index'] = index + 1
        await show_edit_weight(update, context, index + 1)
    
    elif action == 'custom':
        context.user_data['awaiting_custom_weight'] = index
        await query.edit_message_text(
            f"Введи точный вес для упражнения:\n"
            f"<b>{weights_to_edit[index]['name']}</b>\n\n"
            f"Текущий вес: {weights_to_edit[index]['current_weight']}кг\n\n"
            f"Введи новый вес (например: 22.5):",
            parse_mode='HTML'
        )
    
    elif action == 'skip':
        context.user_data['edit_index'] = index + 1
        await show_edit_weight(update, context, index + 1)

async def handle_custom_weight_input(update: Update, context: CallbackContext):
    """Обработка ввода пользовательского веса"""
    user_id = update.effective_user.id
    text = update.message.text
    
    index = context.user_data.get('awaiting_custom_weight')
    
    if index is None:
        await update.message.reply_text("❌ Ошибка. Начни редактирование заново.")
        return
    
    try:
        new_weight = float(text)
        if new_weight < 0:
            new_weight = 0.0
        
        weights_to_edit = context.user_data.get('weights_to_edit', [])
        if index < len(weights_to_edit):
            weights_to_edit[index]['current_weight'] = new_weight
        
        await update.message.reply_text(f"✅ Вес установлен: {new_weight}кг")
        
        # Переходим к следующему упражнению
        context.user_data['edit_index'] = index + 1
        context.user_data.pop('awaiting_custom_weight', None)
        
        # Создаем fake update для продолжения
        class FakeQuery:
            def __init__(self, message):
                self.message = message
        
        fake_query = FakeQuery(update.message)
        
        await show_edit_weight(type('FakeUpdate', (), {'callback_query': fake_query})(), context, index + 1)
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введи число (например: 22.5):")

async def show_workout(update: Update, context: CallbackContext, week_key: str, day_key: str):
    """Показать тренировку"""
    if hasattr(update, 'callback_query'):
        query = update.callback_query
    else:
        query = None
    
    week_data = TRAINING_PROGRAM[week_key]
    day_data = week_data[day_key]
    week_weights = week_data['week_weights']
    
    # Формируем текст тренировки
    text = f"<b>📋 {day_data['code']} • {day_data['name']}</b>\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(exercise['name'], exercise['percentage'])
            text += f"{i}. <b>{exercise['name']}</b>\n"
            text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
            
            if 'alternative' in exercise and exercise['alternative']:
                if "присед" in exercise['name'].lower():
                    alt_weight = week_weights.get('leg_extension', 54)
                    text += f"   ИЛИ: Разгибание бедра {alt_weight}кг\n"
            
        elif exercise['type'] == 'accessory':
            text += f"{i}. {exercise['name']}\n"
            if 'key' in exercise:
                weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
                if exercise['reps'] != '-' and exercise['sets'] != '-':
                    text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
                else:
                    text += f"   {weight}кг\n"
            else:
                if exercise['reps'] != '-' and exercise['sets'] != '-':
                    text += f"   {exercise['reps']} × {exercise['sets']}\n"
        
        text += "\n"
    
    week_num = week_data['number']
    day_num = int(day_key.split('_')[1])
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("✅ Тренировка завершена", callback_data=f"complete:{week_num}:{day_num}")],
        [InlineKeyboardButton("← К дням недели", callback_data=f"menu:days:{week_num}")],
        [InlineKeyboardButton("🏁 Выбрать неделю", callback_data="menu:weeks")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_completed_day(update: Update, context: CallbackContext, week_key: str, day_key: str):
    """Показать завершенную тренировку"""
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
            if exercise['reps'] != '-' and exercise['sets'] != '-':
                text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        
        text += "\n"
    
    week_num = week_data['number']
    
    keyboard = [
        [InlineKeyboardButton("← К дням недели", callback_data=f"menu:days:{week_num}")],
        [InlineKeyboardButton("🏁 Выбрать неделю", callback_data="menu:weeks")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def complete_workout(update: Update, context: CallbackContext):
    """Отметить тренировку как завершенную"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(':')
    week_num = int(data_parts[1])
    day_num = int(data_parts[2])
    
    week_key = f"week_{week_num}"
    day_key = f"day_{day_num}"
    
    # Добавляем день в завершенные
    if week_key in TRAINING_PROGRAM:
        if 'completed_days' not in TRAINING_PROGRAM[week_key]:
            TRAINING_PROGRAM[week_key]['completed_days'] = []
        
        if day_key not in TRAINING_PROGRAM[week_key]['completed_days']:
            TRAINING_PROGRAM[week_key]['completed_days'].append(day_key)
    
    # Показываем обновленное меню дней
    await show_days_menu(update, context, week_num)

async def handle_menu_navigation(update: Update, context: CallbackContext):
    """Обработка навигации по меню"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(':')
    menu_type = data_parts[1]
    
    if menu_type == 'weeks':
        await show_weeks_menu(update, context)
    elif menu_type == 'days':
        week_num = int(data_parts[2])
        await show_days_menu(update, context, week_num)

async def cancel(update: Update, context: CallbackContext):
    """Отмена действия"""
    await update.message.reply_text("Действие отменено. Нажми /start для начала.")

def main():
    # Railway: берем токен из переменных окружения
    TOKEN = os.getenv('BOT_TOKEN')  # Изменено с TELEGRAM_TOKEN на BOT_TOKEN
    
    if not TOKEN:
        logger.error("❌ Ошибка: BOT_TOKEN не найден!")
        logger.error("Добавьте в Railway Variables: BOT_TOKEN = ваш_токен")
        return
    
    try:
        # Используем старую версию API для совместимости
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel))
        
        # Обработчики callback-запросов
        application.add_handler(CallbackQueryHandler(show_days_menu, pattern=r'^week:\d+$'))
        application.add_handler(CallbackQueryHandler(handle_day_selection, pattern=r'^(start|view):\d+:\d+$'))
        application.add_handler(CallbackQueryHandler(handle_weights_decision, pattern=r'^weights:(use_current|edit)$'))
        application.add_handler(CallbackQueryHandler(handle_weight_edit, pattern=r'^weight:(set|custom|skip):\d+(:[\d.]+)?$'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern=r'^complete:\d+:\d+$'))
        application.add_handler(CallbackQueryHandler(handle_menu_navigation, pattern=r'^menu:(weeks|days:\d+)$'))
        
        # Обработчик ввода пользовательского веса
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_weight_input))
        
        logger.info("🚀 Бот программы 'Жим 150' запускается...")
        logger.info(f"✅ Токен получен (первые 10 символов): {TOKEN[:10]}...")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка запуска: {e}")

if __name__ == '__main__':
    main()
