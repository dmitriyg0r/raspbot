import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import datetime

# Функция для чтения данных из Excel
def read_schedule(file_path: str):
    df = pd.read_excel(file_path)
    return df

# Определение текущей недели (четная/нечетная)
def get_week_type():
    current_date = datetime.datetime.now()
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
        [KeyboardButton("Расписание на сегодня")],
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

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Расписание на сегодня":
        await today_schedule(update, context)
    elif text == "Показать всё расписание":
        await full_schedule(update, context)

def main():
    # Токен бота
    application = Application.builder().token('7660329675:AAHFxjjHYZyHoP2hZbjWqLvLVwLhU2WlAjQ').build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today_schedule))
    application.add_handler(CommandHandler("full", full_schedule))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
