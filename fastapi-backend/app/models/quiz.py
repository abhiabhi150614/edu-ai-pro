from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database.db import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), index=True)
    month_index = Column(Integer)  # 1-based
    day = Column(Integer)          # 1-30

    title = Column(String)
    questions = Column(JSONB)  # [{question, options:[...], correct_index}]
    required_score = Column(Integer, default=70)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), index=True)
    month_index = Column(Integer)
    day = Column(Integer)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), index=True)
    answers = Column(JSONB)  # [selected_index,...]
    question_results = Column(JSONB)  # [{question_index, user_answer, correct_answer, is_correct, explanation}]
    score = Column(Integer)
    passed = Column(Integer)  # 0/1
    attempt_number = Column(Integer, default=1)  # Track which attempt this is
    time_taken = Column(Integer, nullable=True)  # Time taken in seconds (optional)
    created_at = Column(DateTime, default=datetime.utcnow)


