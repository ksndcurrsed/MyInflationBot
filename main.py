import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import FSInputFile, BufferedInputFile
import matplotlib.pyplot as plt
import numpy as np
import io
import requests
from bs4 import BeautifulSoup

TOKEN = ""

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных
def init_db():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        month TEXT,
                        food REAL DEFAULT 0,
                        transport REAL DEFAULT 0,
                        housing REAL DEFAULT 0,
                        clothing REAL DEFAULT 0,
                        entertainment REAL DEFAULT 0,
                        health REAL DEFAULT 0,
                        education REAL DEFAULT 0
                    )''')
    conn.commit()
    conn.close()

init_db()

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Рассчитать инфляцию"), KeyboardButton(text="💾 Миф")],
        [KeyboardButton(text="📈 Инфляция Росстат"), KeyboardButton(text="✏️ Ввести расходы")],
        [KeyboardButton(text="🗑 Удалить запись")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_handler(message: Message):
    message_text = (
        "👋 Привет! Я чат-бот <b>Моя инфляция</b>, и я помогу вам разобраться, "
        "насколько ваши ощущения об инфляции совпадают с реальными данными.\n\n"
        "📊 Многие думают, что цены растут быстрее, чем показывает Росстат. "
        "Но на самом деле инфляция считается по широкой корзине товаров и услуг, "
        "а личные траты у каждого разные. Если вы чаще покупаете подорожавшие товары, "
        "вам может казаться, что инфляция выше. Психология тоже играет роль: "
        "мы замечаем рост цен сильнее, чем их снижение.\n\n"
        "❓ <b>Хотите узнать, какая инфляция именно у вас?</b> Давайте вместе посчитаем! "
        "Я помогу вам рассчитать вашу личную инфляцию и сравнить её с официальной."
    )
    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile('./images/start.png', 'rb'), caption=message_text, reply_markup=main_menu, parse_mode="HTML")

@dp.message(lambda message: message.text == "✏️ Ввести расходы")
async def input_expenses(message: Message):
    await message.answer("📌 Отправь свои расходы за этот месяц в формате:\n📅 месяц (числом, например, 03 для марта)\n🍽️ еда\n🚌 транспорт\n🏠 жилье\n👕 одежда\n🎉 развлечения\n❤️ здоровье\n📚 образование\n\nПример: 02 15000 2000 22000 1000 8000 3000 10000")

@dp.message(lambda message: message.text == "🗑 Удалить запись")
async def delete_expense_prompt(message: Message):
    await message.answer("❌ Введите <b>месяц</b> (например, 03 для марта), за который хотите удалить данные.", parse_mode="HTML")

@dp.message(lambda message: message.text.isdigit() and len(message.text) == 2)
async def delete_expense(message: Message):
    user_id = message.from_user.id
    month = message.text
    
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE user_id = ? AND month = ?", (user_id, month))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Данные за месяц <b>{month}</b> удалены!", parse_mode="HTML")

@dp.message(lambda message: message.text == "💾 Миф")
async def send_myth(message: Message):
    message_text = (
    '📈 Как видите, расчёт вашей личной инфляции может отличаться от общих данных, '
    'но это не значит, что официальная статистика неверна. Росстат использует проверенные методики, '
    'учитывая цены тысяч товаров и услуг по всей стране. Если ваша личная инфляция выше, это может '
    'быть связано с вашими покупательскими привычками или тем, что некоторые товары дорожают быстрее других.\n\n'
    '💰 Экономические факты для повышения финансовой грамотности:\n\n'
    '💵 Инфляция – это не только рост цен, но и изменение покупательной способности денег. '
    'Чтобы защитить свои сбережения, важно инвестировать, а не просто хранить деньги "под подушкой".\n\n'
    '🛒 Разные категории товаров дорожают по-разному. Например, цены на электронику могут '
    'снижаться из-за технологического прогресса, а продукты питания – расти из-за сезонности и мировых рынков.\n\n'
    '🏦 Банковские вклады и инвестиции помогают компенсировать инфляцию. Депозиты с процентами, '
    'облигации или акции могут сохранить и приумножить ваши деньги.\n\n'
    '✅ Теперь у вас есть не только расчёт личной инфляции, но и полезные знания, '
    'которые помогут вам разумнее управлять финансами!'
    )
    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile('./images/myth.png', 'rb'))
    await message.answer(text=message_text)

@dp.message(lambda message: message.text == "📈 Инфляция Росстат")
async def key_index_send(message: Message):
    url = 'https://cbr.ru/key-indicators/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    inflation_values = soup.find_all("div", class_="value")  # Найти все элементы
    key_inflation = inflation_values[1].text.strip()
    print(inflation_values)
    month_values = soup.find_all("div", class_="denotement")
    print(month_values)
    key_month = month_values[1].text.strip()
    message_text = "📈 Текущий показатель инфляции от ЦБ РФ на " + key_month + " год составляет: " + key_inflation
    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile('./images/rosstat.png', 'rb'), caption=message_text)



@dp.message(lambda message: message.text == "📊 Рассчитать инфляцию")
async def calculate_inflation(message: Message):
    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile('./images/inflation.png', 'rb'))
    user_id = message.from_user.id
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY month DESC LIMIT 2", (user_id,))
    records = cursor.fetchall()
    
    if len(records) == 0:
        await message.answer("📌 Отправь свои расходы за этот и прошлый месяц в формате:\n📅 месяц (числом, например, 03 для марта)\n🍽️ еда\n🚌 транспорт\n🏠 жилье\n👕 одежда\n🎉 развлечения\n❤️ здоровье\n📚 образование\n\nПример: 02 15000 2000 22000 1000 8000 3000 10000\n03 15000 3000 22500 800 4000 11000")
        return
    elif len(records) == 1:
        await message.answer("📌 Отправь свои расходы за этот месяц в формате:\n📅 месяц (числом, например, 03 для марта)\n🍽️ еда\n🚌 транспорт\n🏠 жилье\n👕 одежда\n🎉 развлечения\n❤️ здоровье\n📚 образование\n\nПример: 02 15000 2000 22000 1000 8000 3000 10000")
        return
    
    last_month = records[-1]
    this_month = records[-2]
    
    last_total = sum(last_month[3:])
    this_total = sum(this_month[3:])
    
    if last_total == 0:
        inflation_rate = "Невозможно рассчитать (нет данных за прошлый месяц)"
    else:
        inflation_rate = ((this_total - last_total) / last_total) * 100
    
    inflation_message = f"📈 Общая личная инфляция: {inflation_rate:.2f}%\n\n"

    last_month_summary = "Сумма расходов за прошлый месяц: " + str(last_total) + "\n"
    this_month_summary = "Сумма расходов за текущий месяц: " + str(this_total) + "\n"
    
    categories = ["Еда", "Транспорт", "Жилье", "Одежда", "Развлечения", "Здоровье", "Образование"]
    last_values = np.array(last_month[3:])
    this_values = np.array(this_month[3:])
    
    recommendations = "\n📌 Персонализированные рекомендации:\n"
    personalized_advice = {
        "Еда": "Попробуй готовить дома чаще – это может сэкономить бюджет.",
        "Транспорт": "Используй общественный транспорт или каршеринг для снижения расходов.",
        "Жилье": "Проверь тарифы ЖКХ, возможно, есть более выгодные предложения.",
        "Одежда": "Подожди сезонных скидок или попробуй second-hand магазины.",
        "Развлечения": "Ты потратил много в этом месяце на развлечения, попробуй городские мероприятия.",
        "Здоровье": "Инвестируй в профилактику – это поможет избежать больших затрат в будущем.",
        "Образование": "Ищи бесплатные онлайн-курсы, чтобы оптимизировать траты."
    }
    
    for i, category in enumerate(categories):
        change = ((this_values[i] - last_values[i]) / last_values[i]) * 100 if last_values[i] != 0 else 0
        if change > 20:
            recommendations += f"⚠️ {category}: Значительное увеличение расходов. {personalized_advice[category]}\n"
        elif 10 <= change <= 20:
            recommendations += f"ℹ️ {category}: Умеренный рост расходов. {personalized_advice[category]}\n"
        elif change < -10:
            recommendations += f"✅ {category}: Отлично! Вы сократили расходы.\n"


    fig, axes = plt.subplots(1, 2, figsize=(10, 5))  # Чуть уменьшил размер для баланса

    colors = plt.cm.Paired.colors  

    # Прошлый месяц
    wedges1, _, autotexts1 = axes[0].pie(
        last_values, autopct='%1.1f%%', colors=colors,
        textprops={'fontsize': 10}, wedgeprops={'edgecolor': 'black'}, pctdistance=1.2
    )
    axes[0].set_title("Прошлый месяц", fontsize=12, pad=15)  # Добавил отступ

    # Текущий месяц
    wedges2, _, autotexts2 = axes[1].pie(
        this_values, autopct='%1.1f%%', colors=colors,
        textprops={'fontsize': 10}, wedgeprops={'edgecolor': 'black'}, pctdistance=1.2
    )
    axes[1].set_title("Текущий месяц", fontsize=12, pad=15)  # Добавил отступ

    # Легенда внизу
    handles = [plt.Line2D([0], [0], color=color, lw=4) for color in colors]
    fig.legend(handles, categories, loc="lower center", ncol=4, fontsize=10)

    plt.subplots_adjust(top=0.85, bottom=0.15)  # Двигаем заголовки внутрь, легенду вниз


    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    photo = BufferedInputFile(buffer.getvalue(), filename="inflation.png")
    
    await message.answer_photo(photo=photo, caption=inflation_message + this_month_summary + last_month_summary + recommendations, reply_markup=main_menu)

# Обработчик данных за один месяц (8 значений)
@dp.message(lambda message: message.text and len(message.text.split()) == 8)
async def handle_one_month_input(message: Message):
    user_id = message.from_user.id
    data = message.text.split()

    try:
        month = data[0]
        expenses = list(map(float, data[1:]))
        
        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM expenses WHERE user_id = ? AND month = ?", (user_id, month))
        existing_record = cursor.fetchone()

        if existing_record:
            await message.answer(f"⚠️ Запись за месяц {month} уже существует. Введите данные заново или уточните месяц.")
        else:
            cursor.execute(
                '''INSERT INTO expenses (user_id, month, food, transport, housing, clothing, entertainment, health, education) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (user_id, month, *expenses)
            )
            conn.commit()
            
            cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY month DESC LIMIT 2", (user_id,))
            records = cursor.fetchall()
            conn.close()

            if len(records) == 2:
                await calculate_inflation(message)
            else:
                await message.answer(f"✅ Данные за {month} сохранены. Теперь введите расходы за второй месяц.")

    except Exception as e:
        logging.error(f"Ошибка при обработке данных: {e}")
        await message.answer("❌ Ошибка! Проверь формат ввода и попробуй снова.")

# Обработчик данных за два месяца (16 значений)
@dp.message(lambda message: message.text and len(message.text.split()) == 16)
async def handle_two_months_input(message: Message):
    user_id = message.from_user.id
    data = message.text.split()

    try:
        month1, expenses1 = data[0], list(map(float, data[1:8]))
        month2, expenses2 = data[8], list(map(float, data[9:]))
        
        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        for month, expenses in [(month1, expenses1), (month2, expenses2)]:
            cursor.execute("SELECT * FROM expenses WHERE user_id = ? AND month = ?", (user_id, month))
            existing_record = cursor.fetchone()

            if not existing_record:
                cursor.execute(
                    '''INSERT INTO expenses (user_id, month, food, transport, housing, clothing, entertainment, health, education) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (user_id, month, *expenses)
                )

        conn.commit()
        conn.close()

        await message.answer("✅ Данные за два месяца сохранены!")
        await calculate_inflation(message)

    except Exception as e:
        logging.error(f"Ошибка при обработке данных: {e}")
        await message.answer("❌ Ошибка! Проверь формат ввода и попробуй снова.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
