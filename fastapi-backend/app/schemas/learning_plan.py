from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class DayTask(BaseModel):
    day: int
    concept: str
    quiz_id: Optional[str] = None
    quiz_min_score: int = 70
    completed: bool = False
    started_at: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None  # Structured AI plan for the day


class MonthPlan(BaseModel):
    index: int
    title: str
    goals: List[str]
    topics: List[str]
    status: str = "locked"  # locked, active, completed
    days: Optional[List[DayTask]] = None


class LearningPlanCreate(BaseModel):
    total_years: int
    plan: Dict[str, Any]


class LearningPlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    total_years: int
    plan: Dict[str, Any]


