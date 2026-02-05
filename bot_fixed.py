import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8533684792:AAE4MJzrCpeG3UFUul4aw5ta8TIN711f_J4"

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
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    keyboard = [
        [InlineKeyboardButton("Неделя 1", callback_data="week:1")],
        [InlineKeyboardButton("Неделя 2", callback_data="week:2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏋️ Выбери неделю:", reply_markup=reply_markup)

async def show_days_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать дни недели"""
    query = update.callback_query
    await query.answer()
    
    try:
        week_num = int(query.data.split(":")[1])
        
        keyboard = [
            [InlineKeyboardButton("День 1", callback_data=f"day:{week_num}:1")],
            [InlineKeyboardButton("День 2", callback_data=f"day:{week_num}:2")],
            [InlineKeyboardButton("День 3", callback_data=f"day:{week_num}:3")],
            [InlineKeyboardButton("← Назад", callback_data="back:weeks")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"📅 Неделя {week_num}\nВыбери день:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в show_days_menu: {e}")
        await query.edit_message_text("❌ Ошибка. Попробуй /start")

async def show_workout_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировку дня"""
    query = update.callback_query
    await query.answer()
    
    try:
        data_parts = query.data.split(":")
        week_num = int(data_parts[1])
        day_num = int(data_parts[2])
        
        week_key = f"week_{week_num}"
        day_key = f"day_{day_num}"
        
        if week_key in TRAINING_PROGRAM and day_key in TRAINING_PROGRAM[week_key]:
            day = TRAINING_PROGRAM[week_key][day_key]
            
            text = f"<b>{day['code']} • {day['name']}</b>\n\n"
            
            for i, ex in enumerate(day['exercises'], 1):
                text += f"{i}. {ex['name']}\n"
                if ex['type'] == 'base':
                    text += f"   {ex['percentage']}% × {ex['reps']} × {ex['sets']}\n"
                elif ex['type'] == 'accessory' and ex['reps'] != '-':
                    text += f"   {ex['reps']} × {ex['sets']}\n"
                text += "\n"
            
            keyboard = [
                [InlineKeyboardButton("← Назад к дням", callback_data=f"week:{week_num}")],
                [InlineKeyboardButton("🏁 Выбрать неделю", callback_data="back:weeks")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Тренировка не найдена")
    except Exception as e:
        logger.error(f"Ошибка в show_workout_day: {e}")
        await query.edit_message_text("❌ Ошибка загрузки тренировки")

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки Назад"""
    query = update.callback_query
    await query.answer()
    
    await start(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.callback_query:
        logger.error(f"Callback data: {update.callback_query.data}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Ошибка. Попробуй /start")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(show_days_menu, pattern=r'^week:[12]$'))
    application.add_handler(CallbackQueryHandler(show_workout_day, pattern=r'^day:[12]:[123]$'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern=r'^back:'))
    application.add_handler(CallbackQueryHandler(error_handler))
    
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Бот запущен")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
