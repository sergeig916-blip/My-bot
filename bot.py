import os
import logging
import sys
import json
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app")

# Состояния для ConversationHandler
SELECT_WEEK, REVIEW_ACCESSORY_WEIGHTS, EDIT_WEIGHT, ENTRY_TEST = range(4)

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ==========
USER_MAXES = {'bench': 117.5, 'squat': 125, 'deadlift': 150}

# Базовые веса для подсобки по неделям (неделя -> упражнение -> вес)
DEFAULT_ACCESSORY_WEIGHTS = {
    1: {
        'fly_flat': 17.5,
        'fly_incline': 17.5,
        'reverse_curl': 25.0,
        'hyperextension_weight': 20.0,
        'horizontal_row': 40.0,
        'vertical_pull': 50.0,
        'lateral_raise': 4.0,
        'rear_delt_fly': 3.0,
        'leg_extension': 54.0
    },
    2: {
        'fly_flat': 18.0,
        'fly_incline': 18.0,
        'reverse_curl': 26.0,
        'hyperextension_weight': 21.0,
        'horizontal_row': 42.0,
        'vertical_pull': 52.0,
        'lateral_raise': 4.5,
        'rear_delt_fly': 3.5,
        'leg_extension': 56.0
    }
}

# Программа тренировок
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

# Хранение пользовательских данных
user_data = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_user_state(user_id: int) -> Dict:
    """Получить состояние пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'completed_days': {},  # week -> [days]
            'completed_weeks': [], # список завершенных недель
            'accessory_weights': DEFAULT_ACCESSORY_WEIGHTS.copy(),
            'current_week': None,
            'editing_exercise': None,
            'editing_weight': None,
            'entry_test_result': None  # результат проходки по жиму
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
    """Создать прогресс-бар для дней недели"""
    progress = ['⬜', '⬜', '⬜']
    for day_num in completed_days:
        if 1 <= day_num <= 3:
            progress[day_num - 1] = '🟩'
    return ''.join(progress)

def get_accessory_exercises_for_week(week_number: int) -> List[Dict]:
    """Получить все подсобные упражнения для недели"""
    exercises = []
    week_data = TRAINING_PROGRAM.get(week_number)
    
    if not week_data:
        return exercises
    
    # Собираем уникальные упражнения из всех дней недели
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
                        'name': exercise['name'],
                        'reps': exercise.get('reps', ''),
                        'sets': exercise.get('sets', '')
                    })
    
    return exercises

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
async def show_week_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выбор недели"""
    user_id = update.effective_user.id
    user_state = get_user_state(user_id)
    
    keyboard = []
    for week_num in [1, 2]:
        label = f"🏋️ Неделя {week_num}"
        # Проверяем, завершена ли неделя (только если все 3 дня завершены)
        completed_days = user_state['completed_days'].get(week_num, [])
        if len(completed_days) == 3:
            label = f"✅ {label}"
        
        keyboard.append([InlineKeyboardButton(label, callback_data=f"select_week:{week_num}")])
    
    keyboard.append([InlineKeyboardButton("📊 Мои максимумы", callback_data="menu:maxes")])
    keyboard.append([InlineKeyboardButton("🔄 Сбросить прогресс", callback_data="reset_progress")])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
            "✅ - неделя завершена\n"
            "Выбери неделю тренировки:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_text(
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
            "✅ - неделя завершена\n"
            "Выбери неделю тренировки:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return SELECT_WEEK

async def handle_select_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора недели"""
    query = update.callback_query
    await query.answer()
    
    # Получаем номер недели из callback_data
    week_number = int(query.data.split(":")[1])
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Сохраняем текущую неделю
    user_state['current_week'] = week_number
    
    # Проверяем, завершена ли неделя
    completed_days = user_state['completed_days'].get(week_number, [])
    
    if len(completed_days) == 3:
        # Неделя уже завершена, показываем дни
        await show_days_for_week(update, context, week_number)
        return SELECT_WEEK
    else:
        # Неделя не завершена, показываем настройку весов
        return await review_accessory_weights(update, context)

async def review_accessory_weights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать веса подсобки для редактирования"""
    query = update.callback_query
    await query.answer()
    
    # Получаем номер недели
    if hasattr(query, 'data') and ":" in query.data:
        week_number = int(query.data.split(":")[1])
    else:
        # Если неделя передана в контексте
        user_id = query.from_user.id
        user_state = get_user_state(user_id)
        week_number = user_state.get('current_week', 1)
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Сохраняем текущую неделю
    user_state['current_week'] = week_number
    
    # Получаем упражнения для этой недели
    exercises = get_accessory_exercises_for_week(week_number)
    user_weights = user_state['accessory_weights'].get(week_number, DEFAULT_ACCESSORY_WEIGHTS[week_number].copy())
    
    # Формируем сообщение
    text = f"<b>📝 Веса для подсобки (Неделя {week_number})</b>\n\n"
    
    keyboard = []
    for i, exercise in enumerate(exercises, 1):
        weight = user_weights.get(exercise['key'], 0)
        text += f"{i}. {exercise['name']}: <b>{weight}кг</b>\n"
        
        # Кнопки для каждого упражнения: название и +/-0.5
        keyboard.append([
            InlineKeyboardButton(
                f"{i}. {exercise['name']}",
                callback_data=f"edit_weight_simple:{week_number}:{exercise['key']}"
            )
        ])
    
    text += "\nНажми на упражнение, чтобы изменить вес, или продолжи с текущими весами:"
    
    keyboard.append([
        InlineKeyboardButton("✅ Продолжить с этими весами", callback_data=f"use_weights:{week_number}")
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Выбрать другую неделю", callback_data="back_to_weeks")
    ])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return REVIEW_ACCESSORY_WEIGHTS

async def edit_weight_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение веса подсобки (упрощенная версия с +/-0.5)"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные
    _, week_str, exercise_key = query.data.split(":")
    week_number = int(week_str)
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Сохраняем какое упражнение редактируем
    user_state['editing_exercise'] = exercise_key
    user_state['current_week'] = week_number
    
    # Находим имя упражнения
    exercises = get_accessory_exercises_for_week(week_number)
    exercise_name = next((e['name'] for e in exercises if e['key'] == exercise_key), exercise_key)
    
    # Текущий вес
    if week_number not in user_state['accessory_weights']:
        user_state['accessory_weights'][week_number] = DEFAULT_ACCESSORY_WEIGHTS[week_number].copy()
    
    current_weight = user_state['accessory_weights'][week_number].get(exercise_key, 0)
    user_state['editing_weight'] = current_weight
    
    text = (
        f"<b>✏️ Изменение веса</b>\n\n"
        f"Упражнение: {exercise_name}\n"
        f"Текущий вес: <b>{current_weight}кг</b>\n\n"
        f"Используй кнопки для изменения (±0.5кг):"
    )
    
    # Создаем клавиатуру с кнопками +/-0.5
    keyboard = [
        [
            InlineKeyboardButton("➖0.5", callback_data=f"adjust_simple:-0.5:{week_number}:{exercise_key}"),
            InlineKeyboardButton(f"{current_weight}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data=f"adjust_simple:0.5:{week_number}:{exercise_key}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад к списку", callback_data=f"back_to_review:{week_number}")
        ]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return EDIT_WEIGHT

async def adjust_weight_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая регулировка веса подсобки +/-0.5"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные
    _, adjustment_str, week_str, exercise_key = query.data.split(":")
    week_number = int(week_str)
    adjustment = float(adjustment_str)
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Получаем текущий вес
    if week_number not in user_state['accessory_weights']:
        user_state['accessory_weights'][week_number] = DEFAULT_ACCESSORY_WEIGHTS[week_number].copy()
    
    current_weight = user_state['accessory_weights'][week_number].get(exercise_key, 0)
    
    # Применяем изменение
    new_weight = current_weight + adjustment
    new_weight = max(0, new_weight)  # Не позволяем отрицательный вес
    new_weight = round(new_weight * 2) / 2  # Округляем до 0.5
    
    # Сохраняем новый вес
    user_state['accessory_weights'][week_number][exercise_key] = new_weight
    user_state['editing_weight'] = new_weight
    
    # Обновляем сообщение с новыми кнопками
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
            InlineKeyboardButton("➖0.5", callback_data=f"adjust_simple:-0.5:{week_number}:{exercise_key}"),
            InlineKeyboardButton(f"{new_weight}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data=f"adjust_simple:0.5:{week_number}:{exercise_key}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад к списку", callback_data=f"back_to_review:{week_number}")
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
    
    # Получаем номер недели
    week_number = int(query.data.split(":")[1])
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Показываем меню дней недели
    await show_days_for_week(update, context, week_number)

async def show_days_for_week(update: Update, context: ContextTypes.DEFAULT_TYPE, week_number: int):
    """Показать дни для недели"""
    user_id = update.effective_user.id
    user_state = get_user_state(user_id)
    
    completed_days = user_state['completed_days'].get(week_number, [])
    progress_bar = create_progress_bar(completed_days)
    
    text = f"📅 <b>Неделя {week_number}</b> [{progress_bar}]\n"
    text += f"Завершено: {len(completed_days)}/3 дней\n\n"
    text += "Выбери день для просмотра тренировки:"
    
    keyboard = []
    for day_num in range(1, 4):
        label = f"День {day_num}"
        if day_num in completed_days:
            label = f"✅ {label}"
        callback_data = f"day:start:{week_number}:{day_num}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("⬅️ Выбрать другую неделю", callback_data="back_to_weeks")])
    
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
    query = update.callback_query
    await query.answer()
    
    _, action, week_num_str, day_num_str = query.data.split(":")
    week_number = int(week_num_str)
    day_number = int(day_num_str)
    
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
    
    keyboard = []
    
    # Проверяем, завершен ли уже этот день
    completed_days = user_state['completed_days'].get(week_number, [])
    if day_number not in completed_days:
        keyboard.append([InlineKeyboardButton("✅ Завершить тренировку", callback_data=f"complete:{week_number}:{day_number}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ К дням недели", callback_data=f"back_to_days:{week_number}")])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def complete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить тренировку (исправленная версия)"""
    query = update.callback_query
    await query.answer()
    
    _, week_num_str, day_num_str = query.data.split(":")
    week_number = int(week_num_str)
    day_number = int(day_num_str)
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Добавляем день в завершенные
    if week_number not in user_state['completed_days']:
        user_state['completed_days'][week_number] = []
    
    if day_number not in user_state['completed_days'][week_number]:
        user_state['completed_days'][week_number].append(day_number)
        user_state['completed_days'][week_number].sort()
    
    # Проверяем, завершена ли неделя
    completed_days = user_state['completed_days'].get(week_number, [])
    
    # Показываем результат
    progress_bar = create_progress_bar(completed_days)
    
    text = f"<b>✅ Тренировка завершена!</b>\n\n📅 <b>Неделя {week_number}</b> [{progress_bar}]\n"
    text += f"Завершено: {len(completed_days)}/3 дней\n\n"
    
    # Если неделя завершена
    if len(completed_days) == 3:
        text += "🎉 <b>Поздравляю! Неделя тренировок завершена!</b>\n\n"
        
        if week_number < 2:  # Если это не последняя неделя
            text += f"Готов перейти к <b>неделе {week_number + 1}</b>?\n"
            keyboard = [
                [InlineKeyboardButton(f"➡️ Перейти к неделе {week_number + 1}", callback_data=f"go_next_week:{week_number + 1}")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="menu:main")]
            ]
        else:  # Если это последняя неделя
            text += "🏆 <b>Ты завершил все недели тренировок!</b>\n\n"
            text += f"📊 <b>Время для проходки по жиму лежа!</b>\n"
            text += f"Предыдущий максимум: <b>{USER_MAXES['bench']}кг</b>\n\n"
            text += f"Установи новый максимум (±0.5кг):"
            
            keyboard = [
                [
                    InlineKeyboardButton("➖0.5", callback_data=f"adj_bench:-0.5"),
                    InlineKeyboardButton(f"{USER_MAXES['bench']}кг", callback_data="noop"),
                    InlineKeyboardButton("➕0.5", callback_data=f"adj_bench:0.5")
                ],
                [
                    InlineKeyboardButton("✅ Подтвердить результат", callback_data=f"confirm_bench:{USER_MAXES['bench']}")
                ]
            ]
    else:
        # Неделя не завершена, показываем кнопки для выбора следующего дня
        keyboard = []
        for day_num in range(1, 4):
            label = f"День {day_num}"
            if day_num in completed_days:
                label = f"✅ {label}"
            callback_data = f"day:start:{week_number}:{day_num}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="menu:main")])
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def go_next_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к следующей неделе (рабочая версия)"""
    query = update.callback_query
    await query.answer()
    
    # Получаем номер следующей недели
    week_number = int(query.data.split(":")[1])
    
    # Сохраняем неделю в состоянии пользователя
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    user_state['current_week'] = week_number
    
    # Показываем настройку весов для следующей недели
    return await review_accessory_weights(update, context)

async def adjust_bench_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регулировка результата проходки по жиму +/-0.5"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные
    _, adjustment_str = query.data.split(":")
    adjustment = float(adjustment_str)
    
    # Применяем изменение к глобальному максимуму
    USER_MAXES['bench'] += adjustment
    USER_MAXES['bench'] = max(50, min(300, USER_MAXES['bench']))  # Ограничиваем от 50 до 300
    USER_MAXES['bench'] = round(USER_MAXES['bench'] * 2) / 2  # Округляем до 0.5
    
    current_max = USER_MAXES['bench']
    
    text = (
        "🏆 <b>Ты завершил все недели тренировок!</b>\n\n"
        f"📊 <b>Время для проходки по жиму лежа!</b>\n"
        f"Предыдущий максимум: <b>{USER_MAXES['bench']}кг</b>\n\n"
        f"Установи новый максимум (±0.5кг):"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➖0.5", callback_data=f"adj_bench:-0.5"),
            InlineKeyboardButton(f"{USER_MAXES['bench']}кг", callback_data="noop"),
            InlineKeyboardButton("➕0.5", callback_data=f"adj_bench:0.5")
        ],
        [
            InlineKeyboardButton("✅ Подтвердить результат", callback_data=f"confirm_bench:{USER_MAXES['bench']}")
        ]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_bench_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение результата проходки по жиму"""
    query = update.callback_query
    await query.answer()
    
    # Получаем результат
    _, result_str = query.data.split(":")
    result = float(result_str)
    
    # Сохраняем результат
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
        [InlineKeyboardButton("🔄 Начать новый цикл", callback_data="start_new_cycle")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="menu:main")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_new_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новый цикл тренировок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = get_user_state(user_id)
    
    # Сбрасываем прогресс тренировок (но сохраняем результат проходки)
    user_state['completed_days'] = {}
    user_state['completed_weeks'] = []
    
    text = (
        "🔄 <b>Новый цикл начат!</b>\n\n"
        f"Твой текущий максимум в жиме: <b>{USER_MAXES['bench']}кг</b>\n"
        "Программа пересчитана под новый вес.\n\n"
        "Выбери неделю для начала:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏋️ Неделя 1", callback_data="select_week:1")],
        [InlineKeyboardButton("🏋️ Неделя 2", callback_data="select_week:2")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECT_WEEK

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
    
    # Показываем результат проходки, если есть
    if user_state.get('entry_test_result'):
        text += f"<b>Последняя проходка по жиму:</b> {user_state['entry_test_result']}кг\n\n"
    
    text += "<i>Для изменения максимумов обратитесь к администратору</i>"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]]
    
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
    
    # Сбрасываем прогресс и веса (но не результат проходки)
    user_state['completed_days'] = {}
    user_state['completed_weeks'] = []
    user_state['accessory_weights'] = DEFAULT_ACCESSORY_WEIGHTS.copy()
    
    keyboard = [
        [InlineKeyboardButton("🏋️ Неделя 1", callback_data="select_week:1")],
        [InlineKeyboardButton("🏋️ Неделя 2", callback_data="select_week:2")]
    ]
    
    await query.edit_message_text(
        "🔄 <b>Прогресс сброшен!</b>\n\n"
        "Все завершенные тренировки и настройки весов очищены.\n"
        f"Текущий максимум в жиме: <b>{USER_MAXES['bench']}кг</b>\n\n"
        "Выбери неделю для начала:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECT_WEEK

async def back_to_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к дням недели"""
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    await show_days_for_week(update, context, week_number)

async def back_to_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к просмотру весов"""
    query = update.callback_query
    await query.answer()
    
    week_number = int(query.data.split(":")[1])
    return await review_accessory_weights(update, context)

async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пустой обработчик для кнопок без действия"""
    query = update.callback_query
    await query.answer()

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
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Создаем ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', show_week_selection),
                CallbackQueryHandler(show_week_selection, pattern='^menu:main$'),
                CallbackQueryHandler(show_week_selection, pattern='^back_to_weeks$')
            ],
            states={
                SELECT_WEEK: [
                    CallbackQueryHandler(handle_select_week, pattern='^select_week:'),
                    CallbackQueryHandler(show_maxes, pattern='^menu:maxes$'),
                    CallbackQueryHandler(reset_progress, pattern='^reset_progress$'),
                    CallbackQueryHandler(show_week_selection, pattern='^menu:main$'),
                    CallbackQueryHandler(go_next_week, pattern='^go_next_week:'),
                    CallbackQueryHandler(confirm_bench_result, pattern='^confirm_bench:'),
                    CallbackQueryHandler(start_new_cycle, pattern='^start_new_cycle$')
                ],
                REVIEW_ACCESSORY_WEIGHTS: [
                    CallbackQueryHandler(edit_weight_simple, pattern='^edit_weight_simple:'),
                    CallbackQueryHandler(start_week_training, pattern='^use_weights:'),
                    CallbackQueryHandler(show_week_selection, pattern='^back_to_weeks$'),
                ],
                EDIT_WEIGHT: [
                    CallbackQueryHandler(adjust_weight_simple, pattern='^adjust_simple:'),
                    CallbackQueryHandler(back_to_review, pattern='^back_to_review:'),
                ],
                ENTRY_TEST: [
                    CallbackQueryHandler(adjust_bench_result, pattern='^adj_bench:'),
                    CallbackQueryHandler(confirm_bench_result, pattern='^confirm_bench:')
                ]
            },
            fallbacks=[
                CommandHandler('start', show_week_selection),
                CallbackQueryHandler(show_week_selection, pattern='^menu:main$')
            ]
        )
        
        # Добавляем ConversationHandler
        application.add_handler(conv_handler)
        
        # Обработчики для дней тренировки
        application.add_handler(CallbackQueryHandler(handle_day_selection, pattern='^day:'))
        application.add_handler(CallbackQueryHandler(complete_workout, pattern='^complete:'))
        application.add_handler(CallbackQueryHandler(back_to_days, pattern='^back_to_days:'))
        
        # Обработчик для кнопок без действия
        application.add_handler(CallbackQueryHandler(noop, pattern='^noop$'))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Приложение создано и настроено")
        
        # Запускаем в режиме webhook
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
