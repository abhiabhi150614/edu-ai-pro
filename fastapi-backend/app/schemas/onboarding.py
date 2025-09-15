from pydantic import BaseModel
from typing import List, Optional

class OnboardingData(BaseModel):
    name: str
    grade: str
    career_goals: List[str]  # Changed from goals to career_goals
    current_skills: List[str]  # Changed from skills to current_skills
    time_commitment: str  # Changed from time_availability to time_commitment
    # Removed: custom_goal, custom_skill, learning_style, subjects

class OnboardingResponse(BaseModel):
    id: int
    user_id: int
    name: str
    grade: str
    career_goals: List[str]
    current_skills: List[str]
    time_commitment: str
