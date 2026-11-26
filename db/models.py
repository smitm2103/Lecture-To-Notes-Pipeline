
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    JSON
)
from sqlalchemy.sql import func

from db_config import Base


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lecture_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    lecture_id = Column(
        Integer,
        ForeignKey("lectures.id"),
        nullable=False
    )

    title = Column(String(255), nullable=False)

    # Stores questions, options, correct answers and explanations.
    questions = Column(JSON, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id"),
        nullable=False
    )

    # Stores the user's selected answers.
    answers = Column(JSON, nullable=False)

    score = Column(Integer, nullable=False)

    total_questions = Column(Integer, nullable=False)

    percentage = Column(Float, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
