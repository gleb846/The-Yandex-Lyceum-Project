from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, PracticeQuestion, ButtonText  # Импортируем нужные модели
from models import File

# Создание подключения к базе данных SQLite
engine = create_engine('sqlite:///mydatabase.db')

# Создание всех таблиц, которые описаны в models.py (если они ещё не созданы)
Base.metadata.create_all(engine)

# Создание сессии для работы с базой
Session = sessionmaker(bind=engine)
session = Session()


# Инициализация одного вопроса (пример)
def init_data():
    question_data = {
        "question": "Сколько будет 2 + 2?",
        "correct_answer": "4",
        "explanation": "2 + 2 = 4"
    }

    exists = session.query(PracticeQuestion).filter_by(question=question_data["question"]).first()
    if not exists:
        pq = PracticeQuestion(**question_data)
        session.add(pq)
        session.commit()
        print("Вопрос добавлен.")
    else:
        print("Вопрос уже есть.")


# Инициализация текстов для 15 кнопок
def init_button_texts():
    buttons = [
        {"button_id": "btn_1", "text": "Среднее арифметическое — это сумма чисел, делённая на их количество, причём в арифметической прогрессии любой член равен среднему соседних, а при добавлении числа меньше среднего значение среднего уменьшается, при добавлении больше — увеличивается; в задаче ЕГЭ-2018 с 100 различными натуральными числами и суммой 5120 доказано, что число 230 не может быть среди них, число 14 обязательно присутствует, а минимальное количество чисел, кратных 14, равно четырём."},
        {"button_id": "btn_2", "text": "Теория по теме 2"},
        {"button_id": "btn_3", "text": "Теория по теме 3"},
        {"button_id": "btn_4", "text": "Теория по теме 4"},
        {"button_id": "btn_5", "text": "Теория по теме 5"},
        {"button_id": "btn_6", "text": "Теория по теме 6"},
        {"button_id": "btn_7", "text": "Теория по теме 7"},
        {"button_id": "btn_8", "text": "Теория по теме 8"},
        {"button_id": "btn_9", "text": "Теория по теме 9"},
        {"button_id": "btn_10", "text": "Теория по теме 10"},
        {"button_id": "btn_11", "text": "Теория по теме 11"},
        {"button_id": "btn_12", "text": "Теория по теме 12"},
        {"button_id": "btn_13", "text": "Теория по теме 13"},
        {"button_id": "btn_14", "text": "Теория по теме 14"},
        {"button_id": "btn_15", "text": "Теория по теме 15"},
    ]

    for btn in buttons:
        exists = session.query(ButtonText).filter_by(button_id=btn["button_id"]).first()
        if not exists:
            session.add(ButtonText(**btn))

    session.commit()
    print("Тексты для кнопок добавлены (если их не было ранее).")


def init_files():
    files_data = [
        {"name": "Документ 1", "file_path": "_19_Вся_теория__4krsn.pdf"},
        {"name": "Документ 2", "file_path": "_19_Теория_чисел__Шпаргалка__518sk.pdf"},
    ]

    for f in files_data:
        exists = session.query(File).filter_by(file_path=f["file_path"]).first()
        if not exists:
            file = File(**f)
            session.add(file)
    session.commit()

def add_file_to_db(filepath):
    session = Session()
    new_file = File(name=filepath.split('/')[-1], file_path=filepath)
    session.add(new_file)
    session.commit()
    session.close()


def update_button_text():
    # Находим кнопку в базе данных
    button = session.query(ButtonText).filter_by(button_id="btn_2").first()

    if button:
        # Обновляем текст
        button.text = ''
        session.commit()
        print("Текст для кнопки btn_2 успешно обновлен.")
    else:
        print("Кнопка с button_id='btn_2' не найдена в базе данных.")


# Вызываем функцию для обновления
update_button_text()


# Запуск при старте файла
if __name__ == "__main__":
    init_data()
    update_button_text()
