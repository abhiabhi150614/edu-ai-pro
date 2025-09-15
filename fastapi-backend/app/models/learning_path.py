from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Indexing
    global_month_index = Column(Integer)  # 1..N across total_years*12
    year_number = Column(Integer)         # 1..total_years
    month_of_year = Column(Integer)       # 1..12

    title = Column(String)
    status = Column(String, default="locked")  # locked, active, completed

    # Day tracking
    current_day = Column(Integer, default=1)  # Current day in this month (1-30)
    days_completed = Column(Integer, default=0)  # Number of completed days
    total_days = Column(Integer, default=30)  # Total days in this month
    
    # Progress tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Day details tracking
    days_data = Column(JSON, nullable=True)  # Store day completion status and scores
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("LearningPlan", backref="paths")
    user = relationship("User", backref="learning_paths")


class DayProgress(Base):
    __tablename__ = "day_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), index=True)
    month_index = Column(Integer, index=True)  # 1-based month index
    day_number = Column(Integer, index=True)   # 1-30 day number
    
    # Progress status
    status = Column(String, default="locked")  # locked, active, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Quiz performance
    quiz_score = Column(Integer, nullable=True)  # Last quiz score
    quiz_attempts = Column(Integer, default=0)  # Number of quiz attempts
    best_score = Column(Integer, nullable=True)  # Best score achieved
    
    # Content tracking
    content_viewed = Column(Boolean, default=False)
    time_spent = Column(Integer, default=0)  # Time spent in seconds
    
    # Navigation tracking
    can_proceed = Column(Boolean, default=False)  # Whether user can move to next day
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="day_progress")
    plan = relationship("LearningPlan", backref="day_progress")


