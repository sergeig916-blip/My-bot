import os
import logging
import sys
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app")

# ========== БЕЛЫЙ СПИСОК ПОЛЬЗОВАТЕЛЕЙ ==========
# Добавьте сюда ID пользователей, которым разрешен доступ
# Чтобы узнать ID пользователя: @userinfobot в Telegram
WHITELIST = [
    123456789,  # Ваш ID (замените на реальный)
    # Добавьте сюда ID друзей для тестирования
]

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
    1: {
        'fly_flat': 17.5, 'fly_incline': 17.5, 'reverse_curl': 25.0,
        'hyperextension_weight': 20.0, 'horizontal_row': 40.0,
        'vertical_pull': 50.0, 'lateral_raise': 4.0, 'rear_delt_fly': 3.0,
        'leg_extension': 54.0
    },
    2: {
        'fly_flat': 18.0, 'fly_incline': 18.0, 'reverse_curl': 26.0,
        'hyperextension_weight': 21.0, 'horizontal_row': 42.0,
        'vertical_pull': 52.0, 'lateral_raise': 4.5, 'rear_delt_fly': 3.5,
        'leg_extension': 56.0
    }
}

TRAINING_PROGRAM = {
    1: {
        "name": "Неделя 1",
        "day_1": {
            "name": "Ноги + Грудь", "code": "Н1Д1",
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
            "name": "Спина + Плечи", "code": "Н1Д2",
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
            "name": "Грудь + Плечи", "code": "Н1Д3",
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
            "name": "Ноги + Грудь", "code": "Н2Д1",
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
            "name": "Спина + Плечи", "code": "Н2Д2",
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
            "name": "Грудь + Плечи", "code": "Н2Д3",
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

# Хранение пользовательских данных
user_data = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def check_access(user_id: int) -> bool:
    """Проверить доступ пользователя"""
    return user_id in WHITELIST

async def check_and_respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверить доступ и ответить если нет прав"""
    user_id = update.effective_user.id
    
    if not check_access(user_id):
        # Записываем попытку доступа в логи
        username = update.effective_user.username or "без username"
        first_name = update.effective_user.first_name or "неизвестно"
        logger.warning(f"Попытка доступа от неподтвержденного пользователя: {user_id} (@{username}, {first_name})")
        
        # Отправляем сообщение пользователю
        message = (
            "🚫 <b>Доступ запрещен</b>\n\n"
            "Это приватный бот. Только избранные пользователи могут им пользоваться.\n\n"
            "Если вы должны иметь доступ, свяжитесь с администратором."
        )
        
        if update.callback_query:
            await update.callback_query.answer("🚫 Доступ запрещен", show_alert=True)
        else:
            await update.message.reply_text(message, parse_mode='HTML')
        
        return False
    
    return True

def get_user_state(user_id: int) -> Dict:
    """Получить состояние пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'completed_days': {},
            'accessory_weights': DEFAULT_ACCESSORY_WEIGHTS.copy(),
            'entry_test_result': None,
            'username': None,
            'first_name': None,
            'last_name': None
        }
    return user_data[user_id]

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

def create_progress_bar(completed_days: List[int]) -> str:
    progress = ['⬜', '⬜', '⬜']
    for day_num in completed_days:
        if 1 <= day_num <= 3:
            progress[day_num - 1] = '🟩'
    return ''.join(progress)

def get_accessory_exercises_for_week(week_number: int) -> List[Dict]:
    exercises = []
    week_data = TRAINING_PROGRAM.get(week_number)
    
    if not week_data:
        return exercises
    
    seen_keys = set()
    
    for day_key in ['day_1', 'day_2', 'day_3']:
        day_data = week_data.get(day_key, {})
        for exercise in day_data.get('exercises', []):
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
    """Команда /start с проверкой доступа"""
    if not await check_and_respond(update, context):
        return
    
    user = update.effective_user
    user_id = user.id
    
    user_state = get_user_state(user_id)
    user_state['username'] = user.username
    user_state['first_name'] = user.first_name
    user_state['last_name'] = user.last_name
    
    # Логируем успешный доступ
    logger.info(f"Пользователь {user_id} (@{user.username}) начал работу с ботом")
    
    if context.args and context.args[0] == 'admin':
        return await show_admin_panel(update, context)
    
    return await show_week_selection(update, context)

async def auto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Автостарт при любом сообщении"""
    if not await check_and_respond(update, context):
        return
    
    # Проверяем, есть ли у пользователя данные
    user_id = update.effective_user.id
    user_state = get_user_state(user_id)
    
    # Если пользователь первый раз, сохраняем данные
    if not user_state['username']:
        user = update.effective_user
        user_state['username'] = user.username
        user_state['first_name'] = user.first_name
        user_state['last_name'] = user.last_name
    
    return await show_week_selection(update, context)

async def show_week_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выбор недели"""
    if not await check_and_respond(update, context):
        return
    
    user_id = update.effective_user.id
    user_state = get_user_state(user_id)
    
    keyboard = []
    for week_num in [1, 2]:
        label = f"🏋️ Неделя {week_num}"
        completed_days = user_state['completed_days'].get(week_num, [])
        if len(completed_days) == 3:
            label = f"✅ {label}"
        
        keyboard.append([InlineKeyboardButton(label, callback_data=f"week:{week_num}")])
    
    keyboard.append([InlineKeyboardButton("📊 Мои максимумы", callback_data="maxes")])
    keyboard.append([InlineKeyboardButton("🔄 Сбросить прогресс", callback_data="reset")])
    keyboard.append([InlineKeyboardButton("👁️‍🗨️ Прогресс учеников", callback_data="admin")])
    
    # Кнопка для добавления пользователя в белый список (только для админа)
    if user_id == WHITELIST[0]:  # Первый ID в списке - главный админ
        keyboard.append([InlineKeyboardButton("➕ Добавить пользователя", callback_data="add_user")])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
            "Выбери неделю тренировки:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
            "Выбери неделю тренировки:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_week_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора недели"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    user_state['current_week'] = week_number
    
    # Проверяем, завершена ли неделя
    completed_days = user_state['completed_days'].get(week_number, [])
    
    if len(completed_days) == 3:
        # Неделя завершена, показываем дни
        await show_days_for_week(update, context, week_number)
    else:
        # Неделя не завершена, показываем настройку весов
        await show_accessory_weights(update, context, week_number)

async def show_accessory_weights(update: Update, context: ContextTypes.DEFAULT_TYPE, week_number: int):
    """Показать веса подсобки"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    exercises = get_accessory_exercises_for_week(week_number)
    user_weights = user_state['accessory_weights'].get(week_number, DEFAULT_ACCESSORY_WEIGHTS[week_number].copy())
    
    text = f"<b>📝 Веса для подсобки (Неделя {week_number})</b>\n\n"
    
    keyboard = []
    for i, exercise in enumerate(exercises, 1):
        weight = user_weights.get(exercise['key'], 0)
        text += f"{i}. {exercise['name']}: <b>{weight}кг</b>\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{i}. {exercise['name']}",
                callback_data=f"edit:{week_number}:{exercise['key']}"
            )
        ])
    
    text += "\nНажми на упражнение, чтобы изменить вес, или продолжи с текущими весами:"
    
    keyboard.append([
        InlineKeyboardButton("✅ Продолжить", callback_data=f"start_week:{week_number}")
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="back")
    ])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение веса"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, week_str, exercise_key = query.data.split(":")
    week_number = int(week_str)
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    exercises = get_accessory_exercises_for_week(week_number)
    exercise_name = next((e['name'] for e in exercises if e['key'] == exercise_key), exercise_key)
    
    if week_number not in user_state['accessory_weights']:
        user_state['accessory_weights'][week_number] = DEFAULT_ACCESSORY_WEIGHTS[week_number].copy()
    
    current_weight = user_state['accessory_weights'][week_number].get(exercise_key, 0)
    
    text = (
        f"<b>✏️ Изменение веса</b>\n\n"
        f"Упражнение: {exercise_name}\n"
        f"Текущий вес: <b>{current_weight}кг</b>\n\n"
        f"Используй кнопки для изменения (±0.5кг):"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖0.5", callback_data=f"adjust:-0.5:{week_number}:{exercise_key}"),
            InlineKeyboardButton(f"{current_weight}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data=f"adjust:0.5:{week_number}:{exercise_key}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"weights:{week_number}")
        ]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def adjust_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регулировка веса"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, adjustment_str, week_str, exercise_key = query.data.split(":")
    week_number = int(week_str)
    adjustment = float(adjustment_str)
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    if week_number not in user_state['accessory_weights']:
        user_state['accessory_weights'][week_number] = DEFAULT_ACCESSORY_WEIGHTS[week_number].copy()
    
    current_weight = user_state['accessory_weights'][week_number].get(exercise_key, 0)
    
    new_weight = current_weight + adjustment
    new_weight = max(0, new_weight)
    new_weight = round(new_weight * 2) / 2
    
    user_state['accessory_weights'][week_number][exercise_key] = new_weight
    
    exercises = get_accessory_exercises_for_week(week_number)
    exercise_name = next((e['name'] for e in exercises if e['key'] == exercise_key), exercise_key)
    
    text = (
        f"<b>✏️ Изменение веса</b>\n\n"
        f"Упражнение: {exercise_name}\n"
        f"Текущий вес: <b>{new_weight}кг</b>\n\n"
        f"Используй кнопки для изменения (±0.5кг):"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖0.5", callback_data=f"adjust:-0.5:{week_number}:{exercise_key}"),
            InlineKeyboardButton(f"{new_weight}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data=f"adjust:0.5:{week_number}:{exercise_key}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"weights:{week_number}")
        ]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_week_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать тренировку недели"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    await show_days_for_week(update, context, week_number)

async def show_days_for_week(update: Update, context: ContextTypes.DEFAULT_TYPE, week_number: int):
    """Показать дни недели"""
    if not await check_and_respond(update, context):
        return
    
    user_id = update.effective_user.id
    user_state = get_user_state(user_id)
    
    completed_days = user_state['completed_days'].get(week_number, [])
    progress_bar = create_progress_bar(completed_days)
    
    text = f"📅 <b>Неделя {week_number}</b> [{progress_bar}]\n"
    text += f"Завершено: {len(completed_days)}/3 дней\n\n"
    
    if len(completed_days) == 3:
        text += "✅ <b>Неделя завершена!</b>\n\n"
    
    text += "Выбери день для просмотра тренировки:"
    
    keyboard = []
    for day_num in range(1, 4):
        label = f"День {day_num}"
        if day_num in completed_days:
            label = f"✅ {label}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"day:{week_number}:{day_num}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора дня"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, week_str, day_str = query.data.split(":")
    week_number = int(week_str)
    day_number = int(day_str)
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    week_data = TRAINING_PROGRAM.get(week_number)
    if not week_data:
        await query.answer("Неделя не найдена")
        return
    
    day_key = f"day_{day_number}"
    if day_key not in week_data:
        await query.answer("День не найден")
        return
    
    day_data = week_data[day_key]
    week_weights = user_state['accessory_weights'].get(week_number, DEFAULT_ACCESSORY_WEIGHTS[week_number])
    
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
    
    keyboard = []
    
    completed_days = user_state['completed_days'].get(week_number, [])
    if day_number not in completed_days:
        keyboard.append([InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_number}:{day_number}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ К дням недели", callback_data=f"days:{week_number}")])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить тренировку"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, week_str, day_str = query.data.split(":")
    week_number = int(week_str)
    day_number = int(day_str)
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    if week_number not in user_state['completed_days']:
        user_state['completed_days'][week_number] = []
    
    if day_number not in user_state['completed_days'][week_number]:
        user_state['completed_days'][week_number].append(day_number)
        user_state['completed_days'][week_number].sort()
    
    completed_days = user_state['completed_days'].get(week_number, [])
    progress_bar = create_progress_bar(completed_days)
    
    text = f"<b>✅ Тренировка завершена!</b>\n\n📅 <b>Неделя {week_number}</b> [{progress_bar}]\n"
    text += f"Завершено: {len(completed_days)}/3 дней\n\n"
    
    if len(completed_days) == 3:
        text += "🎉 <b>Поздравляю! Неделя тренировок завершена!</b>\n\n"
        
        if week_number < 2:
            text += f"Готов перейти к <b>неделе {week_number + 1}</b>?\n"
            keyboard = [
                [InlineKeyboardButton(f"➡️ Перейти к неделе {week_number + 1}", callback_data=f"week:{week_number + 1}")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="back")]
            ]
        else:
            text += "🏆 <b>Ты завершил все недели тренировок!</b>\n\n"
            text += f"📊 <b>Время для проходки по жиму лежа!</b>\n"
            text += f"Предыдущий максимум: <b>{USER_MAXES['bench']}кг</b>\n\n"
            text += f"Установи новый максимум (±0.5кг):"
            
            keyboard = [
                [
                    InlineKeyboardButton("➖0.5", callback_data="bench:-0.5"),
                    InlineKeyboardButton(f"{USER_MAXES['bench']}кг", callback_data="noop"),
                    InlineKeyboardButton("➕0.5", callback_data="bench:0.5")
                ],
                [
                    InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_bench:{USER_MAXES['bench']}")
                ]
            ]
    else:
        keyboard = []
        for day_num in range(1, 4):
            label = f"День {day_num}"
            if day_num in completed_days:
                label = f"✅ {label}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"day:{week_number}:{day_num}")])
        
        keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="back")])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def adjust_bench(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регулировка жима"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, adjustment_str = query.data.split(":")
    adjustment = float(adjustment_str)
    
    USER_MAXES['bench'] += adjustment
    USER_MAXES['bench'] = max(50, min(300, USER_MAXES['bench']))
    USER_MAXES['bench'] = round(USER_MAXES['bench'] * 2) / 2
    
    text = (
        "🏆 <b>Ты завершил все недели тренировок!</b>\n\n"
        f"📊 <b>Время для проходки по жиму лежа!</b>\n"
        f"Предыдущий максимум: <b>{USER_MAXES['bench']}кг</b>\n\n"
        f"Установи новый максимум (±0.5кг):"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖0.5", callback_data="bench:-0.5"),
            InlineKeyboardButton(f"{USER_MAXES['bench']}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data="bench:0.5")
        ],
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_bench:{USER_MAXES['bench']}")
        ]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_bench(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтвердить результат жима"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    _, result_str = query.data.split(":")
    result = float(result_str)
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    user_state['entry_test_result'] = result
    
    text = (
        "🏆 <b>Отличный результат!</b>\n\n"
        f"Твой новый максимум в жиме лежа: <b>{result}кг</b>\n\n"
        "Теперь программа будет использовать этот вес для расчета тренировок.\n\n"
        "<b>Что дальше?</b>\n"
        "• Начать новый цикл тренировок с обновленным максимумом\n"
        "• Или сделать перерыв и продолжить позже\n\n"
        "<i>Твой прогресс сохранен</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Начать новый цикл", callback_data="new_cycle")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="back")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_new_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новый цикл"""
    if not await check_and_respond(update, context):
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    user_state['completed_days'] = {}
    
    text = (
        "🔄 <b>Новый цикл начат!</b>\n\n"
        f"Твой текущий максимум в жиме: <b>{USER_MAXES['bench']}кг</b>\n"
        "Программа пересчитана под новый вес.\n\n"
        "Выбери неделю для начала:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏋️ Неделя 1", callback_data="week:1")],
        [InlineKeyboardButton("🏋️ Неделя 2", callback_data="week:2")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_maxes(update: Update, context: ContextTypes
