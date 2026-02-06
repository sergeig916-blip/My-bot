import os
import json
import logging
import sys
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ========== КОНСТАНТЫ И ПЕРЕЧИСЛЕНИЯ ==========
class CallbackAction(Enum):
    BACK = "back"
    WEEK = "week"
    MAXES = "maxes"
    RESET = "reset"
    ADMIN = "admin"
    EDIT = "edit"
    ADJUST = "adjust"
    WEIGHTS = "weights"
    START_WEEK = "start_week"
    DAY = "day"
    COMPLETE = "complete"
    DAYS = "days"
    BENCH = "bench"
    CONFIRM_BENCH = "confirm_bench"
    NEW_CYCLE = "new_cycle"
    NOOP = "noop"
    MARK_SET = "mark_set"

class ExerciseType(Enum):
    BASE = "base"
    ACCESSORY = "accessory"

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_IDS = json.loads(os.environ.get("ADMIN_IDS", "[]"))

# ========== МОДЕЛИ ДАННЫХ ==========
@dataclass
class Exercise:
    type: ExerciseType
    name: str
    percentage: Optional[float] = None
    reps: Optional[str] = None
    sets: Optional[str] = None
    key: Optional[str] = None
    completed_sets: int = 0

@dataclass
class TrainingDay:
    name: str
    code: str
    exercises: List[Exercise]

@dataclass
class WeekProgram:
    name: str
    day_1: TrainingDay
    day_2: TrainingDay
    day_3: TrainingDay

@dataclass
class UserState:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    completed_days: Dict[int, List[int]] = None
    accessory_weights: Dict[int, Dict[str, float]] = None
    entry_test_result: Optional[float] = None
    last_active: Optional[str] = None
    
    def __post_init__(self):
        if self.completed_days is None:
            self.completed_days = {}
        if self.accessory_weights is None:
            self.accessory_weights = {}

# ========== МЕНЕДЖЕР ДАННЫХ ==========
class DataManager:
    _instance = None
    _user_states: Dict[int, UserState] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_user_state(self, user_id: int) -> UserState:
        if user_id not in self._user_states:
            self._user_states[user_id] = UserState(
                user_id=user_id,
                last_active=datetime.now().isoformat()
            )
        else:
            self._user_states[user_id].last_active = datetime.now().isoformat()
        return self._user_states[user_id]
    
    def save_user_state(self, user_state: UserState):
        self._user_states[user_state.user_id] = user_state
    
    def get_all_users(self) -> List[UserState]:
        return list(self._user_states.values())
    
    def reset_user_progress(self, user_id: int):
        if user_id in self._user_states:
            self._user_states[user_id].completed_days = {}
            # Сброс весов до дефолтных значений происходит в другом месте

# ========== ЗАГРУЗКА КОНФИГУРАЦИИ ==========
def load_config() -> Tuple[Dict, Dict, Dict]:
    """Загрузка конфигурации из JSON файлов"""
    try:
        with open('training_program.json', 'r', encoding='utf-8') as f:
            training_program = json.load(f)
        
        with open('default_weights.json', 'r', encoding='utf-8') as f:
            default_weights = json.load(f)
        
        with open('user_maxes.json', 'r', encoding='utf-8') as f:
            user_maxes = json.load(f)
        
        # Конвертация в объекты
        program = {}
        for week_num, week_data in training_program.items():
            program[int(week_num)] = WeekProgram(
                name=week_data['name'],
                day_1=TrainingDay(
                    name=week_data['day_1']['name'],
                    code=week_data['day_1']['code'],
                    exercises=[Exercise(**ex) for ex in week_data['day_1']['exercises']]
                ),
                day_2=TrainingDay(
                    name=week_data['day_2']['name'],
                    code=week_data['day_2']['code'],
                    exercises=[Exercise(**ex) for ex in week_data['day_2']['exercises']]
                ),
                day_3=TrainingDay(
                    name=week_data['day_3']['name'],
                    code=week_data['day_3']['code'],
                    exercises=[Exercise(**ex) for ex in week_data['day_3']['exercises']]
                )
            )
        
        return program, default_weights, user_maxes
        
    except FileNotFoundError:
        # Загрузка из кода (запасной вариант)
        return _load_default_config()

def _load_default_config():
    """Запасная загрузка конфигурации"""
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
    
    # Конвертация старого формата в новый
    program = {}
    # ... (конвертация TRAINING_PROGRAM в WeekProgram объекты)
    
    return program, DEFAULT_ACCESSORY_WEIGHTS, USER_MAXES

# ========== КЭШ И УТИЛИТЫ ==========
class CacheManager:
    def __init__(self):
        self._cache = {}
        self._weight_cache = {}
    
    def get_cached_weight(self, exercise_name: str, percentage: float) -> float:
        cache_key = f"{exercise_name}_{percentage}"
        if cache_key not in self._weight_cache:
            weight = self._calculate_weight_uncached(exercise_name, percentage)
            self._weight_cache[cache_key] = weight
        return self._weight_cache[cache_key]
    
    def _calculate_weight_uncached(self, exercise_name: str, percentage: float) -> float:
        exercise_lower = exercise_name.lower()
        USER_MAXES = load_config()[2]
        
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
    
    def clear_cache(self):
        self._cache.clear()
        self._weight_cache.clear()

# ========== ФОРМАТТЕРЫ ДЛЯ ВИЗУАЛЬНЫХ УЛУЧШЕНИЙ ==========
class MessageFormatter:
    @staticmethod
    def format_exercise_box(exercise: Exercise, weight: Optional[float] = None, 
                          total_sets: int = 0, completed_sets: int = 0) -> str:
        """Форматирование упражнения в рамке"""
        emoji = "🏋️" if exercise.type == ExerciseType.BASE else "💪"
        color_start = "🟦" if exercise.type == ExerciseType.BASE else "🟩"
        
        sets_display = ""
        if total_sets > 0:
            sets_progress = "✅" * completed_sets + "⬜" * (total_sets - completed_sets)
            sets_display = f"\n{sets_progress} ({completed_sets}/{total_sets})"
        
        weight_display = ""
        if weight is not None:
            weight_display = f"\n📊 Вес: {weight}кг"
        elif exercise.key:
            weight_display = "\n📊 Вес: настроить"
        
        reps_sets = ""
        if exercise.reps and exercise.sets:
            reps_sets = f"\n🔢 {exercise.reps} × {exercise.sets}"
        elif exercise.reps:
            reps_sets = f"\n🔢 {exercise.reps}"
        
        return (
            f"{color_start}┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"{emoji} {exercise.name}"
            f"{weight_display}"
            f"{reps_sets}"
            f"{sets_display}\n"
            f"{color_start}┗━━━━━━━━━━━━━━━━━━━━━┛"
        )
    
    @staticmethod
    def format_training_day(day: TrainingDay, week_weights: Dict[str, float], 
                          completed_sets: Dict[str, int]) -> str:
        """Форматирование всего дня тренировки"""
        header = f"📅 <b>{day.code} • {day.name}</b>\n\n"
        exercises_text = []
        
        for i, exercise in enumerate(day.exercises, 1):
            weight = None
            if exercise.type == ExerciseType.BASE and exercise.percentage:
                weight = CacheManager().get_cached_weight(exercise.name, exercise.percentage)
            elif exercise.type == ExerciseType.ACCESSORY and exercise.key:
                weight = week_weights.get(exercise.key, 0)
            
            completed = completed_sets.get(f"{day.code}_{i}", 0)
            total_sets = int(exercise.sets) if exercise.sets and exercise.sets.isdigit() else 0
            
            exercises_text.append(
                f"{i}. {MessageFormatter.format_exercise_box(exercise, weight, total_sets, completed)}"
            )
        
        return header + "\n\n".join(exercises_text)
    
    @staticmethod
    def create_progress_bar(completed_days: List[int]) -> str:
        """Создание графического прогресс-бара"""
        progress = ['⬜', '⬜', '⬜']
        for day_num in completed_days:
            if 1 <= day_num <= 3:
                progress[day_num - 1] = '🟩'
        return ''.join(progress)
    
    @staticmethod
    async def show_loading_indicator(query, text: str = "Загрузка..."):
        """Показать индикатор загрузки"""
        try:
            await query.edit_message_text(
                f"⏳ {text}",
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(0.3)  # Имитация загрузки
        except:
            pass

# ========== КЛАВИАТУРЫ ==========
class KeyboardBuilder:
    @staticmethod
    def build_week_selection(user_state: UserState) -> InlineKeyboardMarkup:
        keyboard = []
        for week_num in [1, 2]:
            label = f"🏋️ Неделя {week_num}"
            completed_days = user_state.completed_days.get(week_num, [])
            if len(completed_days) == 3:
                label = f"✅ {label}"
            
            keyboard.append([
                InlineKeyboardButton(
                    label, 
                    callback_data=f"{CallbackAction.WEEK.value}:{week_num}"
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("📊 Мои максимумы", callback_data=CallbackAction.MAXES.value)],
            [InlineKeyboardButton("🔄 Сбросить прогресс", callback_data=CallbackAction.RESET.value)],
            [InlineKeyboardButton("👁️‍🗨️ Прогресс учеников", callback_data=CallbackAction.ADMIN.value)]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_exercise_controls(week_number: int, day_number: int, exercise_index: int, 
                              completed_sets: int, total_sets: int) -> InlineKeyboardMarkup:
        """Клавиатура для отметки выполненных подходов"""
        keyboard = []
        
        if completed_sets < total_sets:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Подход {completed_sets + 1}/{total_sets}",
                    callback_data=f"{CallbackAction.MARK_SET.value}:{week_number}:{day_number}:{exercise_index}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{CallbackAction.DAYS.value}:{week_number}")
        ])
        
        return InlineKeyboardMarkup(keyboard)

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
class BotHandlers:
    def __init__(self):
        self.data_manager = DataManager()
        self.cache_manager = CacheManager()
        self.formatter = MessageFormatter()
        self.keyboard_builder = KeyboardBuilder()
        
        self.training_program, self.default_weights, self.user_maxes = load_config()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        user_state = self.data_manager.get_user_state(user.id)
        
        user_state.username = user.username
        user_state.first_name = user.first_name
        user_state.last_name = user.last_name
        
        self.data_manager.save_user_state(user_state)
        
        if context.args and context.args[0] == 'admin':
            return await self.show_admin_panel(update, context)
        
        return await self.show_week_selection(update, context)
    
    async def show_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор недели"""
        user_id = update.effective_user.id
        user_state = self.data_manager.get_user_state(user_id)
        
        keyboard = self.keyboard_builder.build_week_selection(user_state)
        
        message = (
            "🏋️‍♂️ <b>Бот программы 'Жим 150'</b>\n\n"
            "Выбери неделю тренировки:"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            await update.callback_query.answer()
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
    
    async def handle_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора недели"""
        query = update.callback_query
        await self.formatter.show_loading_indicator(query, "Загружаем данные...")
        
        week_number = int(query.data.split(":")[1])
        user_state = self.data_manager.get_user_state(query.from_user.id)
        user_state.current_week = week_number
        
        completed_days = user_state.completed_days.get(week_number, [])
        
        if len(completed_days) == 3:
            await self.show_days_for_week(update, context, week_number)
        else:
            await self.show_accessory_weights(update, context, week_number)
    
    async def mark_set_completed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отметить выполненный подход"""
        query = update.callback_query
        await query.answer()
        
        _, week_str, day_str, ex_str = query.data.split(":")
        week_number = int(week_str)
        day_number = int(day_str)
        exercise_index = int(ex_str) - 1
        
        # Здесь должна быть логика сохранения выполненного подхода
        # Временно просто показываем сообщение
        await query.answer("✅ Подход отмечен!")
        
        # Обновляем сообщение
        await self.handle_day_selection(update, context)
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора с проверкой прав"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id not in ADMIN_IDS and not ADMIN_IDS:
            await query.answer("⛔ Доступ запрещен")
            return
        
        users = self.data_manager.get_all_users()
        
        if not users:
            text = "📊 <b>Панель администратора</b>\n\nПока нет активных пользователей."
        else:
            text = "<b>📊 Прогресс учеников:</b>\n\n"
            
            for user_state in users:
                username = user_state.username or "Без username"
                first_name = user_state.first_name or ""
                last_name = user_state.last_name or ""
                
                user_info = f"{first_name} {last_name}".strip()
                if user_info:
                    user_info = f" ({user_info})"
                
                total_completed = 0
                for week in [1, 2]:
                    completed_days = user_state.completed_days.get(week, [])
                    total_completed += len(completed_days)
                
                entry_result = user_state.entry_test_result
                entry_text = f", Проходка: {entry_result}кг" if entry_result else ""
                
                text += f"👤 @{username}{user_info}\n"
                text += f"   Завершено: {total_completed}/6 дней{entry_text}\n"
                text += f"   Последняя активность: {user_state.last_active[:10]}\n\n"
        
        keyboard = [[
            InlineKeyboardButton("🏠 В главное меню", callback_data=CallbackAction.BACK.value)
        ]]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
def setup_logging():
    """Настройка расширенного логирования"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Логирование важных действий в отдельный файл
    audit_logger = logging.getLogger('audit')
    audit_handler = logging.FileHandler('audit.log', encoding='utf-8')
    audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    return logging.getLogger(__name__), audit_logger

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    logger, audit_logger = setup_logging()
    logger.info("🚀 Запуск бота...")
    
    try:
        # Проверка токена
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не установлен")
            return
        
        application = Application.builder().token(BOT_TOKEN).build()
        handlers = BotHandlers()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler('start', handlers.start))
        
        # Основные callback обработчики
        application.add_handler(CallbackQueryHandler(
            handlers.show_week_selection, 
            pattern=f"^{CallbackAction.BACK.value}$"
        ))
        application.add_handler(CallbackQueryHandler(
            handlers.handle_week_selection, 
            pattern=f"^{CallbackAction.WEEK.value}:"
        ))
        application.add_handler(CallbackQueryHandler(
            handlers.mark_set_completed,
            pattern=f"^{CallbackAction.MARK_SET.value}:"
        ))
        application.add_handler(CallbackQueryHandler(
            handlers.show_admin_panel,
            pattern=f"^{CallbackAction.ADMIN.value}$"
        ))
        
        # Обработчик ошибок
        application.add_error_handler(lambda u, c: logger.error(f"Ошибка: {c.error}"))
        
        logger.info("✅ Приложение создано и настроено")
        
        # Webhook или polling
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
            logger.info(f"🌐 Настройка webhook на: {webhook_url}")
            
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=webhook_url,
                drop_pending_updates=True
            )
        else:
            logger.info("🔄 Запуск в режиме polling")
            application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
