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

# ========== ДАННЫЕ ПО УМОЛЧАНИЮ ==========
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

# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Получить или создать пользователя"""
    if not DATABASE_URL:
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING *
        """, (user_id, username, first_name, last_name))
        
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return user
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        return None

def get_user_maxes(user_id: int):
    """Получить максимумы пользователя"""
    if not DATABASE_URL:
        return {'bench': 117.5, 'squat': 125, 'deadlift': 150}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT bench_max, squat_max, deadlift_max
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return {
                'bench': float(result['bench_max']),
                'squat': float(result['squat_max']),
                'deadlift': float(result['deadlift_max'])
            }
        return {'bench': 117.5, 'squat': 125, 'deadlift': 150}
    except Exception as e:
        logger.error(f"Ошибка при получении максимумов: {e}")
        return {'bench': 117.5, 'squat': 125, 'deadlift': 150}

def get_or_create_training_week(user_id: int, week_number: int):
    """Получить или создать неделю тренировок"""
    if not DATABASE_URL:
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Сначала получаем/создаем пользователя
        get_or_create_user(user_id)
        
        # Получаем или создаем неделю
        cur.execute("""
            INSERT INTO training_weeks (user_id, week_number, week_weights)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, week_number) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """, (user_id, week_number, json.dumps(DEFAULT_ACCESSORY_WEIGHTS)))
        
        week = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return week
    except Exception as e:
        logger.error(f"Ошибка при создании недели: {e}")
        return None

def update_week_weights(user_id: int, week_number: int, weights: dict):
    """Обновить веса для недели"""
    if not DATABASE_URL:
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE training_weeks
            SET week_weights = %s, weights_set = TRUE
            WHERE user_id = %s AND week_number = %s
            RETURNING *
        """, (json.dumps(weights), user_id, week_number))
        
        week = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return week
    except Exception as e:
        logger.error(f"Ошибка при обновлении весов: {e}")
        return None

def mark_day_completed(user_id: int, week_number: int, day_number: int):
    """Отметить день как завершенный"""
    if not DATABASE_URL:
        return []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем текущие завершенные дни
        cur.execute("""
            SELECT completed_days
            FROM training_weeks
            WHERE user_id = %s AND week_number = %s
        """, (user_id, week_number))
        
        result = cur.fetchone()
        completed_days = result['completed_days'] if result and result['completed_days'] else []
        if isinstance(completed_days, str):
            completed_days = json.loads(completed_days)
        
        # Добавляем день, если его еще нет
        if day_number not in completed_days:
            completed_days.append(day_number)
            
            cur.execute("""
                UPDATE training_weeks
                SET completed_days = %s
                WHERE user_id = %s AND week_number = %s
            """, (json.dumps(completed_days), user_id, week_number))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return completed_days
    except Exception as e:
        logger.error(f"Ошибка при отметке дня: {e}")
        return []

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def calculate_weight(user_id: int, exercise_name: str, percentage: float):
    """Расчет веса для базового упражнения"""
    maxes = get_user_maxes(user_id)
    exercise_lower = exercise_name.lower()
    
    if "жим" in exercise_lower and "лежа" in exercise_lower:
        base = maxes['bench']
    elif "присед" in exercise_lower:
        base = maxes['squat']
    elif "становая" in exercise_lower:
        base = maxes['deadlift']
    elif "стоя" in exercise_lower:
        base = maxes['bench'] * 0.6
    else:
        base = maxes['bench']
    
    weight = base * percentage / 100
    return round(weight / 2.5) * 2.5

def create_progress_bar(completed_days):
    """Создание прогресс-бара для недели"""
    progress = ['⬜', '⬜', '⬜']
    for day_num in completed_days:
        if 1 <= day_num <= 3:
            progress[day_num - 1] = '🟩'
    return ''.join(progress)

def get_unique_accessory_exercises(week_number: int):
    """Получить уникальные упражнения подсобки для недели"""
    exercises = []
    seen_keys = set()
    
    week_data = TRAINING_PROGRAM.get(week_number)
    if not week_data:
        return exercises
    
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
    """Команда /start - главное меню"""
    user = update.effective_user
    
    # Регистрируем пользователя
    get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
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
    """Показать максимумы пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    maxes = get_user_maxes(user_id)
    
    text = (
        "<b>📊 Твои максимумы:</b>\n\n"
        f"• Жим лежа: {maxes['bench']}кг\n"
        f"• Присед: {maxes['squat']}кг\n"
        f"• Становая: {maxes['deadlift']}кг\n\n"
        "<i>Для изменения максимумов обратитесь к администратору</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_week_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора недели"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "menu:main":
        keyboard = [
            [InlineKeyboardButton("🏋️ Неделя 1", callback_data="menu:week:1")],
            [InlineKeyboardButton("🏋️ Неделя 2", callback_data="menu:week:2")],
            [InlineKeyboardButton("📊 Мои максимумы", callback_data="menu:maxes")]
        ]
        text = "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\nВыбери неделю тренировки:"
    
    else:
        week_number = int(query.data.split(":")[2])
        week_data = get_or_create_training_week(user_id, week_number)
        
        completed_days = []
        if week_data and week_data.get('completed_days'):
            completed_days_data = week_data['completed_days']
            if isinstance(completed_days_data, str):
                completed_days = json.loads(completed_days_data)
            else:
                completed_days = completed_days_data
        
        progress_bar = create_progress_bar(completed_days)
        
        keyboard = []
        for day_num in range(1, 4):
            if day_num in completed_days:
                label = f"✅ День {day_num}"
                callback_data = f"day:view:{week_number}:{day_num}"
            else:
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
    """Обработка выбора дня тренировки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, action, week_num_str, day_num_str = query.data.split(":")
    week_number = int(week_num_str)
    day_number = int(day_num_str)
    
    context.user_data['current_week'] = week_number
    context.user_data['current_day'] = day_number
    context.user_data['user_id'] = user_id
    
    # Получаем данные недели
    week_data = get_or_create_training_week(user_id, week_number)
    
    completed_days = []
    if week_data and week_data.get('completed_days'):
        completed_days_data = week_data['completed_days']
        if isinstance(completed_days_data, str):
            completed_days = json.loads(completed_days_data)
        else:
            completed_days = completed_days_data
    
    # Если день уже завершен, показываем его
    if action == 'view' or day_number in completed_days:
        await show_completed_day(query, week_number, day_number, user_id)
        return
    
    # Проверяем, установлены ли веса для недели
    weights_set = week_data.get('weights_set', False) if week_data else False
    
    if not weights_set:
        await ask_about_weights(query, week_number, user_id, context)
    else:
        await show_workout(query, week_number, day_number, user_id)

async def ask_about_weights(query, week_number: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Спросить про веса подсобки для недели"""
    week_data = get_or_create_training_week(user_id, week_number)
    
    week_weights = DEFAULT_ACCESSORY_WEIGHTS.copy()
    if week_data and week_data.get('week_weights'):
        weights_data = week_data['week_weights']
        if isinstance(weights_data, str):
            week_weights = json.loads(weights_data)
        else:
            week_weights = weights_data
    
    accessory_exercises = get_unique_accessory_exercises(week_number)
    
    weights_text = f"<b>🏋️ Веса подсобки для недели {week_number}:</b>\n\n"
    
    for i, exercise in enumerate(accessory_exercises, 1):
        weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
        weights_text += f"{i}. {exercise['name']}: {weight}кг\n"
    
    context.user_data['accessory_exercises'] = accessory_exercises
    context.user_data['edit_index'] = 0
    context.user_data['week_weights'] = week_weights
    
    keyboard = [
        [InlineKeyboardButton("✅ Оставить эти веса", callback_data=f"weights:keep:{week_number}")],
        [InlineKeyboardButton("✏️ Изменить веса", callback_data=f"weights:edit:{week_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        weights_text + "\nИспользовать эти веса для всей недели?",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_weights_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка решения по весам"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, decision, week_num_str = query.data.split(":")
    week_number = int(week_num_str)
    
    if decision == 'keep':
        week_weights = context.user_data.get('week_weights', DEFAULT_ACCESSORY_WEIGHTS)
        update_week_weights(user_id, week_number, week_weights)
        await show_workout(query, week_number, 1, user_id)
    
    elif decision == 'edit':
        await edit_weight(query, week_number, user_id, context, 0)

async def edit_weight(query, week_number: int, user_id: int, context: ContextTypes.DEFAULT_TYPE, index: int):
    """Редактирование веса конкретного упражнения"""
    accessory_exercises = context.user_data.get('accessory_exercises', [])
    week_weights = context.user_data.get('week_weights', DEFAULT_ACCESSORY_WEIGHTS.copy())
    
    if index >= len(accessory_exercises):
        update_week_weights(user_id, week_number, week_weights)
        await show_workout(query, week_number, 1, user_id)
        return
    
    exercise = accessory_exercises[index]
    current_weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
    
    keyboard = [
        [
            InlineKeyboardButton("➖2.5кг", callback_data=f"weight:change:{week_number}:{index}:-2.5"),
            InlineKeyboardButton("➖5кг", callback_data=f"weight:change:{week_number}:{index}:-5"),
            InlineKeyboardButton("➖7.5кг", callback_data=f"weight:change:{week_number}:{index}:-7.5")
        ],
        [
            InlineKeyboardButton(f"✅ {current_weight}кг", callback_data=f"weight:skip:{week_number}:{index}")
        ],
        [
            InlineKeyboardButton("➕2.5кг", callback_data=f"weight:change:{week_number}:{index}:2.5"),
            InlineKeyboardButton("➕5кг", callback_data=f"weight:change:{week_number}:{index}:5"),
            InlineKeyboardButton("➕7.5кг", callback_data=f"weight:change:{week_number}:{index}:7.5")
        ],
        [InlineKeyboardButton("⏭ Пропустить", callback_data=f"weight:skip:{week_number}:{index}")]
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
    """Обработка изменения веса"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, _, week_num_str, index_str, change_str = query.data.split(":")
    week_number = int(week_num_str)
    index = int(index_str)
    change = float(change_str)
    
    accessory_exercises = context.user_data.get('accessory_exercises', [])
    week_weights = context.user_data.get('week_weights', DEFAULT_ACCESSORY_WEIGHTS.copy())
    
    if 0 <= index < len(accessory_exercises):
        exercise = accessory_exercises[index]
        current_weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
        new_weight = max(0, current_weight + change)
        
        week_weights[exercise['key']] = new_weight
        context.user_data['week_weights'] = week_weights
        
        await edit_weight(query, week_number, user_id, context, index + 1)

async def handle_weight_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск редактирования веса"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, _, week_num_str, index_str = query.data.split(":")
    week_number = int(week_num_str)
    index = int(index_str)
    
    await edit_weight(query, week_number, user_id, context, index + 1)

async def show_workout(query, week_number: int, day_number: int, user_id: int):
    """Показать тренировку дня"""
    week_data = TRAINING_PROGRAM.get(week_number)
    if not week_data:
        await query.answer("Неделя не найдена")
        return
    
    day_key = f"day_{day_number}"
    if day_key not in week_data:
        await query.answer("День не найден")
        return
    
    day_data = week_data[day_key]
    
    # Получаем веса для недели
    week_db_data = get_or_create_training_week(user_id, week_number)
    week_weights = DEFAULT_ACCESSORY_WEIGHTS.copy()
    if week_db_data and week_db_data.get('week_weights'):
        weights_data = week_db_data['week_weights']
        if isinstance(weights_data, str):
            week_weights = json.loads(weights_data)
        else:
            week_weights = weights_data
    
    text = f"<b>📋 {day_data['code']} • {day_data['name']}</b>\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(user_id, exercise['name'], exercise['percentage'])
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
    
    keyboard = [
        [InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_number}:{day_number}")],
        [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"menu:week:{week_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def show_completed_day(query, week_number: int, day_number: int, user_id: int):
    """Показать завершенную тренировку"""
    week_data = TRAINING_PROGRAM.get(week_number)
    if not week_data:
        await query.answer("Неделя не найдена")
        return
    
    day_key = f"day_{day_number}"
    if day_key not in week_data:
        await query.answer("День не найден")
        return
    
    day_data = week_data[day_key]
    
    # Получаем веса для недели
    week_db_data = get_or_create_training_week(user_id, week_number)
    week_weights = DEFAULT_ACCESSORY_WEIGHTS.copy()
    if week_db_data and week_db_data.get('week_weights'):
        weights_data = week_db_data['week_weights']
        if isinstance(weights_data, str):
            week_weights = json.loads(weights_data)
        else:
            week_weights = weights_data
    
    text = f"<b>✅ {day_data['code']} (завершено)</b>\n\n"
    
    for i, exercise in enumerate(day_data['exercises'], 1):
        if exercise['type'] == 'base':
            weight = calculate_weight(user_id, exercise['name'], exercise['percentage'])
            text += f"{i}. <b>{exercise['name']}</b>\n"
            text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        elif exercise['type'] == 'accessory' and 'key' in exercise:
            weight = week_weights.get(exercise['key'], DEFAULT_ACCESSORY_WEIGHTS.get(exercise['key'], 0))
            text += f"{i}. {exercise['name']}\n"
            if exercise['reps'] != '3 подхода':
                text += f"   {weight}кг × {exercise['reps']} × {exercise['sets']}\n"
        
        text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К дням недели", callback_data=f"menu:week:{week_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить тренировку как завершенную"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, week_num_str, day_num_str = query.data.split(":")
    week_number = int(week_num_str)
    day_number = int(day_num_str)
    
    mark_day_completed(user_id, week_number, day_number)
    await show_week_menu(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуй /start")
    except:
        pass

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
            logger.info(f"🤖 Бот запущен в режиме webhook на порту {PORT}")
            
            # Запускаем сервер с правильными параметрами для Railway
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url="",  # Не нужно, уже настроен выше
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
