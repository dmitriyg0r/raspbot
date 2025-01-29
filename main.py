import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, JobQueue
import datetime
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, time, timezone
import pytz  # добавим для работы с часовыми поясами

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для чтения данных из Excel
def read_schedule(file_path: str):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        logger.error(f"Ошибка при чтении файла расписания: {str(e)}")
        return pd.DataFrame()

# Определение текущей недели (четная/нечетная)
def get_week_type():
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]
    return "четная" if week_number % 2 == 0 else "нечетная"

# Словарь для преобразования английских названий дней в русские
WEEKDAYS = {
    0: 'понедельник',
    1: 'вторник',
    2: 'среда',
    3: 'четверг',
    4: 'пятница',
    5: 'суббота',
    6: 'воскресенье'
}

# Создаем клавиатуру
def get_keyboard():
    keyboard = [
        [KeyboardButton("Расписание на сегодня"), KeyboardButton("Расписание на завтра")],
        [KeyboardButton("Показать всё расписание")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот расписания. Используйте кнопки ниже:",
        reply_markup=get_keyboard()
    )

# Обработчик команды /today
async def today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    week_type = get_week_type()
    current_day = WEEKDAYS[datetime.datetime.now().weekday()]
    
    schedule_df = read_schedule('schedule.xlsx')
    # Приводим значения к нижнему регистру
    schedule_df['Неделя'] = schedule_df['Неделя'].str.lower()
    schedule_df['День недели'] = schedule_df['День недели'].str.lower()
    
    today_schedule = schedule_df[
        (schedule_df['Неделя'] == week_type) & 
        (schedule_df['День недели'] == current_day)
    ]
    
    if today_schedule.empty:
        await update.message.reply_text("На сегодня занятий нет")
    else:
        response = f"Расписание на сегодня ({current_day}, {week_type} неделя):\n\n"
        # Сортируем по времени
        today_schedule = today_schedule.sort_values('Время')
        for _, row in today_schedule.iterrows():
            response += f"🕐 {row['Время']}\n"
            response += f"📚 {row['Предмет']}\n"
            response += f"🏛 Кабинет: {row['Кабинет']}\n\n"
        
        await update.message.reply_text(response)

# Добавляем функцию для показа полного расписания
async def full_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule_df = read_schedule('schedule.xlsx')
    
    # Приводим значения в колонке 'Неделя' к нижнему регистру
    schedule_df['Неделя'] = schedule_df['Неделя'].str.lower()
    # Приводим значения в колонке 'День недели' к нижнему регистру
    schedule_df['День недели'] = schedule_df['День недели'].str.lower()
    
    response = "📚 ПОЛНОЕ РАСПИСАНИЕ:\n\n"
    
    for week_type in ['четная', 'нечетная']:
        response += f"=== {week_type.upper()} НЕДЕЛЯ ===\n\n"
        week_schedule = schedule_df[schedule_df['Неделя'] == week_type]
        
        for day in ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота']:
            day_schedule = week_schedule[week_schedule['День недели'] == day]
            
            if not day_schedule.empty:
                response += f"📅 {day.upper()}:\n"
                # Сортируем по времени
                day_schedule = day_schedule.sort_values('Время')
                for _, row in day_schedule.iterrows():
                    response += f"🕐 {row['Время']}\n"
                    response += f"📚 {row['Предмет']}\n"
                    response += f"🏛 Кабинет: {row['Кабинет']}\n\n"
                response += "---------------\n"
    
    # Разделяем сообщение, если оно слишком длинное
    if len(response) > 4096:
        parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(response)

# Добавляем функцию для показа расписания на завтра
async def tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Исправляем использование datetime
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_weekday = WEEKDAYS[tomorrow.weekday()]
    
    # Определяем тип недели
    week_type = get_week_type()
    # Если завтра будет новая неделя
    if datetime.now().weekday() == 6:  # если сегодня воскресенье
        week_type = "четная" if week_type == "нечетная" else "нечетная"
    
    schedule_df = read_schedule('schedule.xlsx')
    schedule_df['Неделя'] = schedule_df['Неделя'].str.lower()
    schedule_df['День недели'] = schedule_df['День недели'].str.lower()
    
    tomorrow_schedule = schedule_df[
        (schedule_df['Неделя'] == week_type) & 
        (schedule_df['День недели'] == tomorrow_weekday)
    ]
    
    if tomorrow_schedule.empty:
        await update.message.reply_text("Завтра занятий нет")
    else:
        response = f"Расписание на завтра ({tomorrow_weekday}, {week_type} неделя):\n\n"
        tomorrow_schedule = tomorrow_schedule.sort_values('Время')
        for _, row in tomorrow_schedule.iterrows():
            response += f"🕐 {row['Время']}\n"
            response += f"📚 {row['Предмет']}\n"
            response += f"🏛 Кабинет: {row['Кабинет']}\n\n"
        
        await update.message.reply_text(response)

# Обновляем обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Расписание на сегодня":
        await today_schedule(update, context)
    elif text == "Расписание на завтра":
        await tomorrow_schedule(update, context)
    elif text == "Показать всё расписание":
        await full_schedule(update, context)

# Добавляем новую функцию для отправки расписания в канал
async def send_schedule_to_channel(context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = os.getenv('CHANNEL_ID')
        logger.info(f"Начинаю отправку расписания в канал {channel_id}")
        
        # Исправляем использование datetime
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_weekday = WEEKDAYS[tomorrow.weekday()]
        
        week_type = get_week_type()
        if datetime.now().weekday() == 6:
            week_type = "четная" if week_type == "нечетная" else "нечетная"
        
        logger.info(f"Подготовка расписания на {tomorrow_weekday}, {week_type} неделя")
        
        schedule_df = read_schedule('schedule.xlsx')
        schedule_df['Неделя'] = schedule_df['Неделя'].str.lower()
        schedule_df['День недели'] = schedule_df['День недели'].str.lower()
        
        tomorrow_schedule = schedule_df[
            (schedule_df['Неделя'] == week_type) & 
            (schedule_df['День недели'] == tomorrow_weekday)
        ]
        
        if tomorrow_schedule.empty:
            message = "Завтра занятий нет"
        else:
            message = f"Расписание на завтра ({tomorrow_weekday}, {week_type} неделя):\n\n"
            tomorrow_schedule = tomorrow_schedule.sort_values('Время')
            for _, row in tomorrow_schedule.iterrows():
                message += f"🕐 {row['Время']}\n"
                message += f"📚 {row['Предмет']}\n"
                message += f"🏛 Кабинет: {row['Кабинет']}\n\n"
        
        logger.info("Отправляю сообщение в канал")
        await context.bot.send_message(chat_id=channel_id, text=message)
        logger.info("Сообщение успешно отправлено")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке расписания: {str(e)}")

async def test_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для немедленной отправки расписания"""
    await send_schedule_to_channel(context)
    await update.message.reply_text("Тестовая отправка выполнена")

def main():
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Настраиваем планировщик с учетом московского времени
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_date = datetime.now(moscow_tz)
    target_time = time(hour=20, minute=0)
    
    # Конвертируем время в UTC для планировщика
    moscow_time = moscow_tz.localize(datetime.combine(current_date, target_time))
    utc_time = moscow_time.astimezone(pytz.UTC).time()
    
    job_queue = application.job_queue
    job_queue.run_daily(
        send_schedule_to_channel,
        time=utc_time,
        days=(0,1,2,3,4,5,6),
        name='daily_schedule'
    )
    
    logger.info(f"Планировщик настроен на отправку в {target_time} по московскому времени (UTC: {utc_time})")
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_send))  # Добавляем тестовую команду
    application.add_handler(CommandHandler("today", today_schedule))
    application.add_handler(CommandHandler("tomorrow", tomorrow_schedule))
    application.add_handler(CommandHandler("full", full_schedule))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Добавляем команду для ручной отправки расписания (для тестирования)
    application.add_handler(CommandHandler("send_schedule", send_schedule_to_channel))
    
    application.run_polling()

if __name__ == '__main__':
    main()
