import os
import json
import logging
import sys
from typing import Dict, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
# Безопасно получаем токен
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    # Временный фолбэк для тестирования
    BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app")

# Загружаем список админов
def load_admin_ids():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return []  # Если файла нет - пустой список

ADMIN_IDS = load_admin_ids()

# ========== ЗАГРУЗКА ДАННЫХ ИЗ JSON ==========
def load_json_data():
    """Загружает данные из JSON файлов"""
    try:
        with open('training_program.json', 'r', encoding='utf-8') as f:
            TRAINING_PROGRAM = json.load(f)
        
        with open('default_weights.json', 'r', encoding='utf-8') as f:
            DEFAULT_ACCESSORY_WEIGHTS = json.load(f)
        
        with open('user_maxes.json', 'r', encoding='utf-8') as f:
            USER_MAXES = json.load(f)
        
        # Конвертируем ключи в int
        TRAINING_PROGRAM = {int(k): v for k, v in TRAINING_PROGRAM.items()}
        DEFAULT_ACCESSORY_WEIGHTS = {int(k): v for k, v in DEFAULT_ACCESSORY_WEIGHTS.items()}
        
        return TRAINING_PROGRAM, DEFAULT_ACCESSORY_WEIGHTS, USER_MAXES
        
    except FileNotFoundError:
        # Возвращаем None, чтобы использовать данные из кода
        return None, None, None

# Загружаем данные
TRAINING_PROGRAM_JSON, DEFAULT_ACCESSORY_WEIGHTS_JSON, USER_MAXES_JSON = load_json_data()

# Используем данные из JSON или из кода
if TRAINING_PROGRAM_JSON:
    TRAINING_PROGRAM = TRAINING_PROGRAM_JSON
    DEFAULT_ACCESSORY_WEIGHTS = DEFAULT_ACCESSORY_WEIGHTS_JSON
    USER_MAXES = USER_MAXES_JSON
    logger = logging.getLogger(__name__)
    logger.info("✅ Данные загружены из JSON файлов")
else:
    # Данные из старого кода
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

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== УТИЛИТЫ ДЛЯ ФОРМАТИРОВАНИЯ ==========
def calculate_weight(exercise_name: str, percentage: float):
    """Рассчитывает рабочий вес для упражнения"""
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
    """Создает графический прогресс-бар"""
    progress = ['⬜', '⬜', '⬜']
    for day_num in completed_days:
        if 1 <= day_num <= 3:
            progress[day_num - 1] = '🟩'
    return ''.join(progress)

def get_accessory_exercises_for_week(week_number: int) -> List[Dict]:
    """Возвращает список подсобных упражнений для недели"""
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

# Хранение пользовательских данных
user_data = {}

def get_user_state(user_id: int) -> Dict:
    """Получить состояние пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'completed_days': {},
            'accessory_weights': DEFAULT_ACCESSORY_WEIGHTS.copy(),
            'entry_test_result': None,
            'username': None,
            'first_name': None,
            'last_name': None,
            'registration_date': datetime.now().isoformat()
        }
    return user_data[user_id]

def get_user_progress_stats(user_id: int) -> Dict:
    """Получает статистику прогресса пользователя"""
    user_state = get_user_state(user_id)
    completed_days = user_state['completed_days']
    
    # Считаем пройденные недели и дни
    completed_weeks = 0
    completed_days_count = 0
    
    for week_num in [1, 2]:
        days_in_week = completed_days.get(week_num, [])
        days_count = len(days_in_week)
        completed_days_count += days_count
        
        # Неделя считается пройденной, если пройдены все 3 дня
        if days_count == 3:
            completed_weeks += 1
    
    # Процент выполнения всей программы (6 дней максимум)
    total_progress = (completed_days_count / 6) * 100 if completed_days_count > 0 else 0
    
    return {
        'completed_weeks': completed_weeks,
        'completed_days': completed_days_count,
        'total_progress': round(total_progress, 1),
        'entry_test_result': user_state.get('entry_test_result')
    }

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_id = user.id
    
    user_state = get_user_state(user_id)
    user_state['username'] = user.username
    user_state['first_name'] = user.first_name
    user_state['last_name'] = user.last_name
    
    if context.args and context.args[0] == 'admin':
        return await show_admin_panel(update, context)
    
    return await show_week_selection(update, context)

async def show_week_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выбор недели"""
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
    keyboard.append([InlineKeyboardButton("📈 Прогресс", callback_data="progress")])  # Изменил название
    keyboard.append([InlineKeyboardButton("🔄 Сбросить прогресс", callback_data="reset")])
    
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

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать прогресс пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Получаем статистику
    stats = get_user_progress_stats(user_id)
    
    text = "<b>📈 Ваш прогресс</b>\n\n"
    
    # Основная статистика
    text += f"✅ <b>Пройдено недель:</b> {stats['completed_weeks']}/2\n"
    text += f"📅 <b>Пройдено дней:</b> {stats['completed_days']}/6\n"
    text += f"📊 <b>Общий прогресс:</b> {stats['total_progress']}%\n\n"
    
    # Детали по неделям
    for week_num in [1, 2]:
        completed_days = user_state['completed_days'].get(week_num, [])
        progress_bar = create_progress_bar(completed_days)
        days_count = len(completed_days)
        
        week_status = "✅ Завершена" if days_count == 3 else f"В процессе ({days_count}/3)"
        
        text += f"<b>Неделя {week_num}:</b> {week_status}\n"
        text += f"           {progress_bar}\n"
    
    # Результат проходки
    if stats['entry_test_result']:
        text += f"\n🏆 <b>Последняя проходка по жиму:</b> {stats['entry_test_result']}кг\n"
    
    # Подсказка
    text += "\n<i>Продолжайте тренировки для достижения цели!</i>"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_week_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора недели"""
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
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    await show_days_for_week(update, context, week_number)

async def show_days_for_week(update: Update, context: ContextTypes.DEFAULT_TYPE, week_number: int):
    """Показать дни недели"""
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
    """Обработка выбора дня с улучшенным форматированием"""
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
    
    # Используем улучшенное форматирование с разделителями
    text = f"<b>📋 {day_data['code']} • {day_data['name']}</b>\n"
    text += "─" * 25 + "\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(exercise['name'], exercise['percentage'])
            
            # Первая строка: упражнение
            text += f"<b>{i}. {exercise['name']}</b>\n"
            # Вторая строка: параметры в скобках
            text += f"   ({weight}кг × {exercise['reps']} × {exercise['sets']})\n"
        
        elif exercise['type'] == 'accessory':
            # Первая строка: упражнение
            text += f"{i}. {exercise['name']}\n"
            
            if 'key' in exercise:
                weight = week_weights.get(exercise['key'], 0)
                if exercise['reps'] != '3 подхода':
                    # Вторая строка: параметры в скобках
                    text += f"   ({weight}кг × {exercise['reps']} × {exercise['sets']})\n"
                else:
                    text += f"   ({exercise['reps']})\n"
            else:
                text += f"   ({exercise['reps']})\n"
        
        # Добавляем разделитель между упражнениями (кроме последнего)
        if i < len(day_data['exercises']):
            text += "―\n"
        else:
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

async def show_maxes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать максимумы"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    text = (
        "<b>📊 Твои максимумы:</b>\n\n"
        f"• Жим лежа: {USER_MAXES['bench']}кг\n"
        f"• Присед: {USER_MAXES['squat']}кг\n"
        f"• Становая: {USER_MAXES['deadlift']}кг\n\n"
    )
    
    if user_state.get('entry_test_result'):
        text += f"<b>Последняя проходка по жиму:</b> {user_state['entry_test_result']}кг\n\n"
    
    text += "<i>Для изменения максимумов обратитесь к администратору</i>"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def reset_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить прогресс"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    user_state['completed_days'] = {}
    user_state['accessory_weights'] = DEFAULT_ACCESSORY_WEIGHTS.copy()
    
    keyboard = [
        [InlineKeyboardButton("🏋️ Неделя 1", callback_data="week:1")],
        [InlineKeyboardButton("🏋️ Неделя 2", callback_data="week:2")]
    ]
    
    await query.edit_message_text(
        "🔄 <b>Прогресс сброшен!</b>\n\n"
        "Все завершенные тренировки и настройки весов очищены.\n"
        f"Текущий максимум в жиме: <b>{USER_MAXES['bench']}кг</b>\n\n"
        "Выбери неделю для начала:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель администратора"""
    query = update.callback_query
    await query.answer()
    
    # Используем специальный путь для админов через /start admin
    # Обычная кнопка "Прогресс" теперь показывает личный прогресс
    await show_progress(update, context)

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад в главное меню"""
    query = update.callback_query
    await query.answer()
    
    await show_week_selection(update, context)

async def handle_noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пустой обработчик"""
    query = update.callback_query
    await query.answer()

async def handle_weights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к весам"""
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    await show_accessory_weights(update, context, week_number)

async def handle_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к дням"""
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    await show_days_for_week(update, context, week_number)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуй /start")
    except:
        pass

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запуск бота на Railway...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        
        # Основные callback обработчики
        application.add_handler(CallbackQueryHandler(handle_back, pattern='^back$'))
        application.add_handler(CallbackQueryHandler(handle_week_selection, pattern='^week:'))
        application.add_handler(CallbackQueryHandler(show_maxes, pattern='^maxes$'))
        application.add_handler(CallbackQueryHandler(show_progress, pattern='^progress$'))  # Добавил обработчик прогресса
        application.add_handler(CallbackQueryHandler(reset_progress, pattern='^reset$'))
        
        # Веса подсобки
        application.add_handler(CallbackQueryHandler(edit_weight, pattern='^edit:'))
        application.add_handler(CallbackQueryHandler(adjust_weight, pattern='^adjust:'))
        application.add_handler(CallbackQueryHandler(handle_weights, pattern='^weights:'))
        application.add_handler(CallbackQueryHandler(start_week_training, pattern='^start_week:'))
        
        # Дни тренировки
        application.add_handler(CallbackQueryHandler(handle_day_selection, pattern='^day:'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        application.add_handler(CallbackQueryHandler(handle_days, pattern='^days:'))
        
        # Проходка по жиму
        application.add_handler(CallbackQueryHandler(adjust_bench, pattern='^bench:'))
        application.add_handler(CallbackQueryHandler(confirm_bench, pattern='^confirm_bench:'))
        application.add_handler(CallbackQueryHandler(start_new_cycle, pattern='^new_cycle$'))
        
        # Пустой обработчик
        application.add_handler(CallbackQueryHandler(handle_noop, pattern='^noop$'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Приложение создано и настроено")
        
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        logger.info(f"🌐 Настройка webhook на: {webhook_url}")
        
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
