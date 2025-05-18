from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base
from sqlalchemy import Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from models import Base  # если это в отдельном файле
from sqlalchemy import LargeBinary
Base = declarative_base()




class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Название файла
    file_path = Column(String, nullable=False)  # Путь к файлу
    data = Column(LargeBinary)


class PracticeQuestion(Base):
    __tablename__ = 'practice_questions'

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    explanation = Column(String)


class ButtonText(Base):
    __tablename__ = 'button_texts'

    id = Column(Integer, primary_key=True)
    button_id = Column(String, unique=True, nullable=False)  # например 'btn_1', 'btn_2' и т.д.
    text = Column(Text, nullable=False)  # текст, который надо показывать пользователю


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)


class Suggestion(Base):
    __tablename__ = 'suggestions'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    username = Column(String)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
