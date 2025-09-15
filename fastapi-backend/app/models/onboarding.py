from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.database.db import Base
from sqlalchemy.orm import relationship

class Onboarding(Base):
    __tablename__ = "onboarding"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String)
    grade = Column(String)
    career_goals = Column(JSONB)  # List of career goals
    current_skills = Column(JSONB)  # List of current skills
    time_commitment = Column(String)  # Daily time commitment

    user = relationship("User", back_populates="onboarding")
