from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    
    # Google OAuth fields
    google_id = Column(String, unique=True, nullable=True)
    google_email = Column(String, nullable=True)
    google_name = Column(String, nullable=True)
    google_picture = Column(String, nullable=True)
    google_access_token = Column(String, nullable=True)  # Store the access token
    google_refresh_token = Column(String, nullable=True)  # Store the refresh token
    is_google_authenticated = Column(Boolean, default=False)
    

    phone_number = Column(String, nullable=True)
    phone_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Learning path tracking
    current_plan_id = Column(Integer, nullable=True)
    current_month_index = Column(Integer, nullable=True)
    current_day = Column(Integer, nullable=True)
    
    # Relationships
    onboarding = relationship("Onboarding", back_populates="user", uselist=False)
    youtube_schedules = relationship("YouTubeSchedule", back_populates="user")
    learning_plans = relationship("LearningPlan", back_populates="user")
