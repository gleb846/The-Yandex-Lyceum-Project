import telebot
from telebot import types
from database import Session
from models import User, Suggestion
from datetime import datetime
from database import Base, engine
from models import User, Suggestion
import random
from models import ButtonText  # Импорт модели
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import PracticeQuestion
import io
from models import File
import requests

# Настройка подключения к базе данных
engine = create_engine('sqlite:///mydatabase.db')
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

bot = telebot.TeleBot('7332111753:AAG05D9vjSpn_ca2xrwxzTDFFNrRKOWKD1A')


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    session = Session()

    # Проверяем, есть ли пользователь
    user = session.query(User).filter_by(telegram_id=message.chat.id).first()
    if not user:
        user = User(
            telegram_id=message.chat.id,
            username=message.from_user.username or message.from_user.first_name
        )
        session.add(user)
        session.commit()
    session.close()
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Профиль', callback_data='profile')
    btn2 = types.InlineKeyboardButton('Теория', callback_data='theory')
    btn3 = types.InlineKeyboardButton('Практика', callback_data='practice')
    btn4 = types.InlineKeyboardButton('Полезные файлы', callback_data='files')
    btn5 = types.InlineKeyboardButton('Предложения', callback_data='offers')
    btn6 = types.InlineKeyboardButton('🏆 Топ-10', callback_data='leaderboard')
    btn7 = types.InlineKeyboardButton('Полезные каналы', callback_data='channels')
    btn8 = types.InlineKeyboardButton('Погода', callback_data='weather')
    markup.add(btn1, btn6)
    markup.add(btn2, btn3)
    markup.add(btn4)
    markup.add(btn7)
    markup.add(btn5)
    markup.add(btn8)
    bot.send_message(message.chat.id,
                     "👋 Привет! Я — бот для подготовки к ЕГЭ по математике!\n📌 Я помогу тебе:\n- 📖 Прокачать знания по математике\n- ❓ Отвечать на вопросы с выбором ответа\n- 📊 Отслеживать прогресс и статистику\n- ✍️ Отправлять предложения и идеи",
                     reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # 1. Обработка предложений
    if user_suggestions.get(chat_id) == "waiting_for_suggestion":
        session = Session()
        suggestion = Suggestion(
            telegram_id=chat_id,
            username=message.from_user.username or message.from_user.first_name,
            text=text
        )
        session.add(suggestion)
        session.commit()
        session.close()

        user_suggestions.pop(chat_id)
        bot.send_message(chat_id, "Спасибо за ваше предложение! 😊")
        return start(message)

    # 2. Завершение практики
    if text.lower() == "завершить":
        user_practice_data.pop(chat_id, None)
        return start(message)

    if user_suggestions.get(chat_id) == "waiting_for_weather":
        weather_info = get_weather(text)
        bot.send_message(chat_id, weather_info)
        user_suggestions.pop(chat_id)
        return start(message)

    # 3. Проверка ответа на задание
    if chat_id in user_practice_data:
        data = user_practice_data[chat_id]
        question_text = data.get("current_question")

        if not question_text:
            return bot.send_message(chat_id, "Произошла ошибка. Попробуй снова.")

        session = Session()
        question_obj = session.query(PracticeQuestion).filter_by(question=question_text).first()
        user = session.query(User).filter_by(telegram_id=chat_id).first()

        if not question_obj or not user:
            session.close()
            return bot.send_message(chat_id, "Произошла ошибка с вопросом или пользователем.")

        if text.strip() == question_obj.correct_answer:
            user.correct_answers += 1
            bot.send_message(chat_id, "✅ Верно! Молодец.")
        else:
            user.incorrect_answers += 1
            bot.send_message(chat_id, f"❌ Неправильно.\nℹ️ Пояснение: {question_obj.explanation}")

        session.commit()
        session.close()

        return start_practice(message)

    # Если ничего не подошло
    bot.send_message(chat_id, "Я не понял ваш ввод. Используйте кнопки меню.")


def get_button_text(button_id):
    session = Session()
    btn_text = session.query(ButtonText).filter_by(button_id=button_id).first()
    session.close()
    return btn_text.text if btn_text else "Текст не найден"


def show_profile(call):
    session = Session()
    user = session.query(User).filter_by(telegram_id=call.message.chat.id).first()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton('Назад', callback_data='back')
    markup.add(back_btn)
    if user:
        profile_text = (
            f"👤 Профиль:\n"
            f"Имя: {user.username}\n"
            f"Дата регистрации: {user.registration_date.strftime('%Y-%m-%d')}\n"
            f"Правильных ответов: {user.correct_answers}\n"
            f"Неправильных ответов: {user.incorrect_answers}"
        )
    else:
        profile_text = "Профиль не найден."

    session.close()
    bot.send_message(call.message.chat.id, profile_text, reply_markup=markup)


def show_leaderboard(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    session = Session()
    top_users = session.query(User).order_by(User.correct_answers.desc()).limit(10).all()
    session.close()

    if not top_users:
        text = "Пока никто не решил задания 😢"
    else:
        text = "🏆 Топ-10 пользователей по правильным ответам:\n\n"
        for i, user in enumerate(top_users, 1):
            text += f"{i}. {user.username or 'Без имени'} — {user.correct_answers} правильных ответов\n"

    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton('Назад', callback_data='back')
    markup.add(back_btn)

    bot.send_message(call.message.chat.id, text, reply_markup=markup)


def start_practice(obj):
    if isinstance(obj, types.Message):
        chat_id = obj.chat.id
    else:
        chat_id = obj.message.chat.id
        bot.delete_message(chat_id, obj.message.message_id)

    session = Session()
    all_questions = session.query(PracticeQuestion).all()
    session.close()

    user_data = user_practice_data.get(chat_id, {"asked": []})
    remaining = [q for q in all_questions if q.question not in user_data["asked"]]

    if not remaining:
        bot.send_message(chat_id, "🎉 Все задания выполнены!")
        return start(obj.message if isinstance(obj, types.CallbackQuery) else obj)

    question_obj = random.choice(remaining)
    user_data["asked"].append(question_obj.question)
    user_data["current_question"] = question_obj.question
    user_practice_data[chat_id] = user_data

    markup = types.InlineKeyboardMarkup()
    finish_btn = types.InlineKeyboardButton("🚪 Завершить", callback_data="finish_practice")
    markup.add(finish_btn)

    bot.send_message(chat_id, f"🧠 Задание:\n{question_obj.question}", reply_markup=markup)


def get_weather(city):
    api_key = "f430450853714c279f8221723251705"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&lang=ru"

    response = requests.get(url)
    if response.status_code != 200:
        return "⚠️ Не удалось получить погоду. Попробуй позже."

    data = response.json()
    location = data["location"]["name"]
    temp_c = data["current"]["temp_c"]
    condition = data["current"]["condition"]["text"]
    feelslike = data["current"]["feelslike_c"]
    wind_kph = data["current"]["wind_kph"]

    return (
        f"🌤 Погода в {location}:\n"
        f"🌡 Температура: {temp_c}°C (ощущается как {feelslike}°C)\n"
        f"💨 Ветер: {wind_kph} км/ч\n"
        f"📝 Состояние: {condition}"
    )


def Main_Menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Среднее арифметическое', callback_data='btn_1')
    btn2 = types.InlineKeyboardButton('Десятичная запись числа', callback_data='btn_2')
    btn3 = types.InlineKeyboardButton('НОД и НОК', callback_data='btn_3')
    btn4 = types.InlineKeyboardButton('Остатки', callback_data='btn_4')
    btn5 = types.InlineKeyboardButton('Сравнение по модулю', callback_data='btn_5')
    btn6 = types.InlineKeyboardButton('Признаки делимости', callback_data='btn_6')
    btn7 = types.InlineKeyboardButton('Диофантовы уравнения', callback_data='btn_7')
    btn8 = types.InlineKeyboardButton('Инвариант и полуинвариант', callback_data='btn_8')
    btn9 = types.InlineKeyboardButton('Принцип крайнего', callback_data='btn_9')
    btn10 = types.InlineKeyboardButton('Турниры', callback_data='btn_10')
    btn11 = types.InlineKeyboardButton('Теория игр', callback_data='btn_11')
    btn12 = types.InlineKeyboardButton('Раскраски', callback_data='btn_12')
    btn13 = types.InlineKeyboardButton('Соответствия и биекция', callback_data='btn_13')
    btn14 = types.InlineKeyboardButton('Принцип Дирихле', callback_data='btn_14')
    btn15 = types.InlineKeyboardButton('Графы', callback_data='btn_15')
    back_btn = types.InlineKeyboardButton('Назад', callback_data='back')
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    markup.add(btn5)
    markup.add(btn6)
    markup.add(btn7)
    markup.add(btn8)
    markup.add(btn9)
    markup.add(btn10)
    markup.add(btn11)
    markup.add(btn12)
    markup.add(btn13)
    markup.add(btn14)
    markup.add(btn15)
    markup.add(back_btn)
    bot.send_message(call.message.chat.id,
                     '📚 Раздел «Теория» \nЗдесь ты найдёшь важные и полезные материалы для подготовки к ЕГЭ. \nМы собрали основные правила, формулы и понятия, которые помогут тебе уверенно справиться с экзаменом.',
                     reply_markup=markup)


user_suggestions = {}
user_practice_data = {}


def Offers(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Напишите, пожалуйста, ваше предложение или идею для улучшения бота.")
    user_suggestions[call.message.chat.id] = "waiting_for_suggestion"


def Files(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton('Назад', callback_data='back')
    markup.add(back_btn)
    # Открываем файл в бинарном режиме ('rb') и отправляем
    with open('_19_Теория_чисел__Шпаргалка__518sk.pdf', 'rb') as file:
        bot.send_document(call.message.chat.id, file)
    with open('_19_Вся_теория__4krsn.pdf', 'rb') as file:
        bot.send_document(call.message.chat.id, file)
    bot.send_message(call.message.chat.id,
                     "📂 Раздел «Полезные файлы» \nЗдесь ты найдёшь различные материалы для подготовки к ЕГЭ — шпаргалки, конспекты, тесты и задания в удобном формате. \nСкачивай и используй их, чтобы учиться эффективно и экономить время!",
                     reply_markup=markup)


def Channels(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton('Школково', url='https://t.me/MO_EGE')
    btn_2 = types.InlineKeyboardButton('100балльный репетитор', url='https://t.me/stopoints')
    btn_3 = types.InlineKeyboardButton('Математик Андрей', url='https://t.me/+FtHYfWjb5K04MWNi')
    btn_4 = types.InlineKeyboardButton('Умскул', url='https://t.me/semreshaet')
    back_btn = types.InlineKeyboardButton('Назад', callback_data='back')
    markup.add(btn_1)
    markup.add(btn_2)
    markup.add(btn_3)
    markup.add(btn_4)
    markup.add(back_btn)
    bot.send_message(call.message.chat.id,
                     "📢 Раздел «Полезные каналы» \nМы собрали для тебя подборку Telegram-каналов, которые помогут в подготовке к ЕГЭ. \nТам — разборы заданий, советы, лайфхаки, теория и свежие материалы от преподавателей и экспертов. Подписывайся и будь в теме!",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_1")
def button_1(call):
    text = get_button_text("btn_1")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_2")
def button_2(call):
    text = get_button_text("btn_2")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_3")
def button_3(call):
    text = get_button_text("btn_3")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_4")
def button_4(call):
    text = get_button_text("btn_4")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_5")
def button_5(call):
    text = get_button_text("btn_5")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_6")
def button_6(call):
    text = get_button_text("btn_6")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_7")
def button_7(call):
    text = get_button_text("btn_7")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_8")
def button_8(call):
    text = get_button_text("btn_8")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_9")
def button_9(call):
    text = get_button_text("btn_9")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_10")
def button_10(call):
    text = get_button_text("btn_10")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_11")
def button_11(call):
    text = get_button_text("btn_11")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_12")
def button_12(call):
    text = get_button_text("btn_12")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_13")
def button_13(call):
    text = get_button_text("btn_13")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_14")
def button_14(call):
    text = get_button_text("btn_14")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "btn_15")
def button_15(call):
    text = get_button_text("btn_15")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)


def back_to_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    start(call.message)  # просто вызываем start, как при команде /start


# Обработчик всех кнопок
@bot.callback_query_handler(func=lambda call: True)
def universal_handler(call):
    if call.data == 'profile':
        show_profile(call)
    elif call.data == 'theory':
        Main_Menu(call)
    elif call.data == 'practice':
        start_practice(call)
    elif call.data == 'files':
        Files(call)
    elif call.data == 'offers':
        Offers(call)
    elif call.data == 'btn_1':
        button_1(call)
    elif call.data == 'btn_2':
        button_2(call)
    elif call.data == 'btn_3':
        button_3(call)
    elif call.data == 'btn_4':
        button_4(call)
    elif call.data == 'btn_5':
        button_5(call)
    elif call.data == 'btn_6':
        button_6(call)
    elif call.data == 'btn_7':
        button_7(call)
    elif call.data == 'btn_8':
        button_8(call)
    elif call.data == 'btn_9':
        button_9(call)
    elif call.data == 'btn_10':
        button_10(call)
    elif call.data == 'btn_11':
        button_11(call)
    elif call.data == 'btn_12':
        button_12(call)
    elif call.data == 'btn_13':
        button_13(call)
    elif call.data == 'btn_14':
        button_14(call)
    elif call.data == 'btn_15':
        button_15(call)
    elif call.data == 'back':
        back_to_start(call)
    elif call.data == "finish_practice":
        back_to_start(call)
    elif call.data == 'leaderboard':
        show_leaderboard(call)
    elif call.data == 'channels':
        Channels(call)
    elif call.data == 'weather':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Введите название города, чтобы узнать погоду.")
        user_suggestions[call.message.chat.id] = "waiting_for_weather"


# Запуск бота
bot.polling(none_stop=True)
