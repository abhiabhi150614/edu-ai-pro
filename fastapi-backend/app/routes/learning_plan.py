from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import threading
from app.database.db import get_db
from app.models.user import User
from app.models.onboarding import Onboarding
from app.models.learning_plan import LearningPlan
from app.models.learning_path import LearningPath
from app.models.quiz import Quiz
from app.schemas.learning_plan import LearningPlanResponse
from app.core.security import decode_token
from app.core.google_services import send_notification_email
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.gemini_ai import chatbot
from datetime import datetime


router = APIRouter()
bearer_scheme = HTTPBearer()


@router.get("/user/current-position")
def get_current_learning_position(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current position data
    current_position = {
        "current_plan_id": user.current_plan_id,
        "current_month_index": user.current_month_index,
        "current_day": user.current_day
    }
    
    # Get additional context if plan exists
    if user.current_plan_id:
        plan = db.query(LearningPlan).filter(LearningPlan.id == user.current_plan_id).first()
        if plan and isinstance(plan.plan, dict) and "months" in plan.plan:
            months = plan.plan.get("months", [])
            if user.current_month_index and 1 <= user.current_month_index <= len(months):
                month = months[user.current_month_index - 1]
                current_position["current_month_title"] = month.get("title")
                
                days = month.get("days", [])
                if user.current_day and 1 <= user.current_day <= len(days):
                    day = days[user.current_day - 1]
                    current_position["current_day_concept"] = day.get("concept")
                    current_position["current_day_completed"] = day.get("completed", False)
    
    return current_position


def _decide_total_years(grade: str) -> int:
    # Heuristics per user request
    if not grade:
        return 1
    g = grade.lower()
    if "4th" in g:
        return 1  # extra 1 year
    if "3rd" in g:
        return 2
    if "2nd" in g:
        return 2
    if "1st" in g:
        return 3
    if "high school" in g:
        return 2
    if "working" in g:
        return 1
    return 2


def _build_prompt(onboarding: Onboarding, total_years: int) -> str:
    return f"""
You are EduAI. Generate a detailed learning plan as structured JSON.

Context:
- Name: {onboarding.name}
- Grade/Level: {onboarding.grade}
- Career Goals: {onboarding.career_goals}
- Current Skills: {onboarding.current_skills}
- Daily Time Commitment: {onboarding.time_commitment}
- Total Years to Plan: {total_years}

Requirements:
1) Output strictly valid JSON with keys: title, total_years, months.
2) months is a list of 12 * total_years items. Each month item must include:
   - index (1-based across all months)
   - title (descriptive month title)
   - goals (array of 3-5 specific learning goals)
   - topics (array of 5-8 specific topics to cover)
   - status (default "locked")
   - description (brief overview of what this month focuses on)
3) Do not generate daily breakdown yet. Only month-level structure now.
4) Tailor to career_goals and current_skills. Be realistic for {onboarding.time_commitment} per day.
5) Create a logical progression from basic to advanced concepts.
6) Each month should build upon previous months' knowledge.

Return only JSON, no markdown.
"""


@router.post("/learning-plan/generate", response_model=LearningPlanResponse)
def generate_learning_plan(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    try:
        user_id = decode_token(credentials.credentials)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        onboarding = db.query(Onboarding).filter(Onboarding.user_id == user.id).first()
        if not onboarding:
            raise HTTPException(status_code=400, detail="Onboarding data required")

        total_years = _decide_total_years(onboarding.grade)

        def _sanitize_and_parse_json(text: str):
            import json, re
            cleaned = text.strip()
            # Remove code fences ```json ... ``` or ``` ... ```
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned)
                cleaned = re.sub(r"\n```\s*$", "", cleaned)
            # Extract outermost braces content
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end > start:
                candidate = cleaned[start:end+1]
            else:
                candidate = cleaned
            # Remove trailing commas before } or ]
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            # Try to load
            return json.loads(candidate)

        prompt = _build_prompt(onboarding, total_years)
        ai = chatbot.model
        data = None
        try:
            raw = ai.generate_content(prompt)
            text = getattr(raw, 'text', '') or ''
            data = _sanitize_and_parse_json(text)
        except Exception:
            data = None

        # Build fallback months if AI parsing failed
        if not data or not isinstance(data, dict) or not data.get('months'):
            total_months = max(1, int(total_years) * 12)
            months_fallback = []
            base_topics = (onboarding.current_skills or 'Foundations').split(',') if onboarding.current_skills else ['Foundations', 'Core Concepts', 'Projects']
            base_goals = (onboarding.career_goals or 'Improve skills').split(',') if onboarding.career_goals else ['Understand fundamentals', 'Practice regularly', 'Build portfolio']
            for idx in range(1, total_months + 1):
                year_number = ((idx - 1) // 12) + 1
                month_of_year = ((idx - 1) % 12) + 1
                months_fallback.append({
                    "index": idx,
                    "title": f"Year {year_number}, Month {month_of_year}",
                    "goals": [g.strip() for g in base_goals[:5] if g.strip()] or ["Master core topics"],
                    "topics": [t.strip() for t in base_topics[:6] if t.strip()] or ["Core Topic"],
                    "status": "locked",
                    "description": f"Focus on { (base_topics[0] if base_topics else 'core topics') } this month"
                })
            data = {
                "title": onboarding.career_goals or "Personalized Learning Plan",
                "total_years": total_years,
                "months": months_fallback
            }

        # Generate months with proper structure
        months_data = data.get('months', [])
        months = []
        for idx, m in enumerate(months_data, start=1):
            month_status = "active" if idx == 1 else "locked"
            month = {
                **m,
                "status": month_status,
                "days": [],
                "days_generated": False
            }
            months.append(month)

        plan = LearningPlan(
            user_id=user.id,
            title=data.get('title', 'Personalized Learning Plan'),
            total_years=data.get('total_years', total_years),
            plan={"months": months}
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Seed LearningPath rows for each month
        for idx, m in enumerate(months, start=1):
            year_number = ((idx - 1) // 12) + 1
            month_of_year = ((idx - 1) % 12) + 1
            path = LearningPath(
                plan_id=plan.id,
                user_id=user.id,
                global_month_index=idx,
                year_number=year_number,
                month_of_year=month_of_year,
                title=m.get('title', f'Month {idx}'),
                status=m.get('status', 'locked'),
                current_day=1,
                days_completed=0,
                total_days=30
            )
            db.add(path)
        db.commit()

        # Pre-generate first month's 30 days and day 1 detail
        months = plan.plan.get("months", [])
        if months:
            first_month = months[0]
            try:
                first_month["days"] = _generate_days_for_month_via_ai(first_month, onboarding)
                first_month["days_generated"] = True
                # Generate day 1 detail
                if first_month["days"]:
                    d1 = first_month["days"][0]
                    try:
                        d1_detail = _generate_day_detail_via_ai(first_month, d1, onboarding)
                        d1["detail"] = d1_detail
                        d1["started_at"] = datetime.utcnow().isoformat()
                        # Auto-generate quiz for day 1
                        try:
                            from app.routes.quiz import _generate_quiz_via_ai  # local import to avoid circular at module load
                            questions = _generate_quiz_via_ai(first_month, d1, onboarding, 10)
                        except Exception:
                            questions = []
                        if questions:
                            quiz = Quiz(
                                user_id=int(user_id),
                                plan_id=plan.id,
                                month_index=1,
                                day=1,
                                title=f"Day 1 Quiz - {d1.get('concept', 'Learning Assessment')}",
                                questions=questions,
                                required_score=d1.get("quiz_min_score", 70)
                            )
                            db.add(quiz)
                            db.commit()
                            db.refresh(quiz)
                            d1["quiz_id"] = quiz.id
                    except Exception as e:
                        print(f"Error generating day 1 detail/quiz: {str(e)}")
                months[0] = first_month
                plan.plan = {"months": months}
                db.commit()
                db.refresh(plan)
            except Exception as e:
                print(f"Error generating first month days: {str(e)}")

        # Update user's current position to first month, first day
        user.current_plan_id = plan.id
        user.current_month_index = 1
        user.current_day = 1
        db.commit()

        # Google Drive: create root folder EDUAI_NAME_LEARNING_MAIN_PATH
        try:
            from app.core.google_services import ensure_drive_folder
            root_name = f"EDUAI_{onboarding.name or 'USER'}_LEARNING_MAIN_PATH"
            ensure_drive_folder(int(user_id), root_name)
        except Exception as gerr:
            print(f"Drive root folder create error: {gerr}")

        return LearningPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            title=plan.title,
            total_years=plan.total_years,
            plan=plan.plan
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate learning plan: {e}")


def _generate_days_for_month_via_ai(month: dict, onboarding: Onboarding) -> list:
    import json

    def _fallback_days() -> list:
        topics = month.get('topics') or [month.get('title', 'Core topic')]
        base_segments = [
            'Introduction and Basics', 'Deep Dive and Theory', 'Practical Examples', 'Hands-on Practice', 'Real-world Application'
        ]
        days = []
        for i in range(1, 31):
            topic = topics[(i - 1) % len(topics)]
            segment = base_segments[(i - 1) % len(base_segments)]
            days.append({
                "day": i,
                "concept": f"{topic} - {segment}",
                "quiz_id": None,
                "quiz_min_score": 70,
                "completed": False,
                "started_at": None,
                "detail": None,
                "time_estimate": 60  # minutes
            })
        return days

    # Try AI; if rate-limited or fails for any reason, use fallback
    try:
        prompt = f"""
Generate a comprehensive 30-day study plan as JSON for this month.

Month Title: {month.get('title')}
Month Description: {month.get('description', '')}
Goals: {month.get('goals')}
Topics: {month.get('topics')}
Daily Time Commitment: {onboarding.time_commitment}
Learner Profile:
- Grade/Level: {onboarding.grade}
- Career Goals: {onboarding.career_goals}
- Current Skills: {onboarding.current_skills}

Rules:
- Output strictly valid JSON with key "days" = list of exactly 30 items.
- Each day item: {{"day": <1-30>, "concept": <detailed learning objective>, "time_estimate": <minutes>, "quiz_id": null, "quiz_min_score": 70, "completed": false, "started_at": null, "detail": null}}
- Create a logical progression: start with fundamentals, build complexity, end with mastery.
- Each concept should be specific and actionable for the given time commitment.
- Include a mix of theory, practice, and application days.
- Ensure concepts build upon each other throughout the month.
- Make concepts detailed enough to generate specific study content later.
- Return only JSON, no markdown.
"""

        ai = chatbot.model
        raw = ai.generate_content(prompt)
        text = raw.text
        try:
            data = json.loads(text)
        except Exception:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                data = json.loads(text[start:end+1])
            else:
                return _fallback_days()

        days = data.get("days", [])
        if not isinstance(days, list) or len(days) < 30:
            return _fallback_days()

        # Normalize to exactly 30 days
        normalized = []
        for idx, d in enumerate(days[:30], start=1):
            normalized.append({
                "day": d.get("day", idx),
                "concept": d.get("concept", f"Day {idx} Learning Objective"),
                "time_estimate": int(d.get("time_estimate", 60)),
                "quiz_id": d.get("quiz_id", None),
                "quiz_min_score": int(d.get("quiz_min_score", 70)),
                "completed": bool(d.get("completed", False)),
                "started_at": d.get("started_at"),
                "detail": d.get("detail")
            })
        return normalized
    except Exception:
        return _fallback_days()


@router.post("/learning-plan/{plan_id}/start-next-month")
def start_next_month(plan_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    months = plan.plan.get("months", [])
    # Disallow starting if an active month exists
    if any((m.get("status") == "active") for m in months):
        raise HTTPException(status_code=400, detail="An active month already exists")

    # Find first locked month
    start_idx = None
    for i, m in enumerate(months):
        status = m.get("status", "locked")
        if status != "completed":
            start_idx = i
            break

    if start_idx is None:
        return {"message": "All months completed", "plan": plan.plan}

    # Generate days if not present
    month = months[start_idx]
    if not month.get("days"):
        onboarding = db.query(Onboarding).filter(Onboarding.user_id == plan.user_id).first()
        if not onboarding:
            raise HTTPException(status_code=400, detail="Onboarding data required")
        month["days"] = _generate_days_for_month_via_ai(month, onboarding)

    # Activate this month; keep future months locked; prior months remain as is
    for i, m in enumerate(months):
        if i == start_idx:
            m["status"] = "active"
        elif i > start_idx and m.get("status") != "completed":
            m["status"] = "locked"

    # Ensure JSON shape is a dict with months array only
    plan.plan = {"months": [dict(m) for m in months]}
    # Update LearningPath status
    active_path = db.query(LearningPath).filter(LearningPath.plan_id == plan.id, LearningPath.global_month_index == (start_idx + 1)).first()
    if active_path:
        from datetime import datetime
        active_path.status = "active"
        active_path.started_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return {"message": "Month started", "plan": plan.plan}


@router.post("/learning-plan/{plan_id}/start-month/{month_index}")
def start_month(plan_id: int, month_index: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")

    month = months[month_index - 1]
    
    # Check if this month can be started (should be locked or first month)
    if month.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Month already completed")
    
    # Generate days if not already generated
    if not month.get("days") or len(month.get("days", [])) == 0:
        onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
        if not onboarding:
            raise HTTPException(status_code=400, detail="Onboarding data required")
        
        # Generate 30 days for this month
        month["days"] = _generate_days_for_month_via_ai(month, onboarding)
        month["days_generated"] = True

    # Activate this month
    month["status"] = "active"
    month["started_at"] = datetime.utcnow().isoformat()
    
    # Update the plan in database
    months[month_index - 1] = month
    plan.plan = {"months": months}
    
    # Update LearningPath status
    learning_path = db.query(LearningPath).filter(
        LearningPath.plan_id == plan_id,
        LearningPath.global_month_index == month_index
    ).first()
    
    if learning_path:
        learning_path.status = "active"
        learning_path.started_at = datetime.utcnow()
        learning_path.current_day = 1
        learning_path.days_completed = 0
        learning_path.total_days = 30
    
    # Update user's current position
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user:
        user.current_plan_id = plan_id
        user.current_month_index = month_index
        user.current_day = 1
    
    # Google Drive: create month folder under root
    try:
        from app.core.google_services import ensure_drive_folder
        root_name = f"EDUAI_{(user.google_name or user.email or 'USER').split(' ')[0]}_LEARNING_MAIN_PATH" if user else "EDUAI_USER_LEARNING_MAIN_PATH"
        root_id = ensure_drive_folder(int(user_id), root_name)
        if root_id:
            ensure_drive_folder(int(user_id), f"MONTH_{month_index}", parent_id=root_id)
    except Exception as gerr:
        print(f"Drive month folder create error: {gerr}")
    
    db.commit()
    db.refresh(plan)
    
    return {
        "message": f"Month {month_index} started successfully",
        "month": month,
        "plan": plan.plan
    }


@router.get("/learning-plan/{plan_id}/month/{month_index}/days")
def get_month_days(plan_id: int, month_index: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == int(user_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")
    
    month = months[month_index - 1]
    days = month.get("days") or []
    
    # Always check if days are generated and fetch from database
    if not month.get("days_generated") or not days or len(days) == 0:
        onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
        if not onboarding:
            raise HTTPException(status_code=400, detail="Onboarding data required")
        
        # Generate days and mark as generated
        month["days"] = _generate_days_for_month_via_ai(month, onboarding)
        month["days_generated"] = True
        months[month_index - 1] = month
        plan.plan = {"months": [dict(m) for m in months]}
        db.commit()
        db.refresh(plan)
        days = month["days"]
    
    return {"days": days, "days_generated": month.get("days_generated", False)}


@router.post("/learning-plan/{plan_id}/activate-month/{month_index}")
def activate_month(plan_id: int, month_index: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")

    # Lock all other months, set selected to active
    for i, m in enumerate(months, start=1):
        m["status"] = "active" if i == month_index else (m.get("status") if i < month_index and m.get("status") == "completed" else "locked")

    plan.plan["months"] = months
    db.commit()
    db.refresh(plan)
    return {"message": "Month activated", "plan": plan.plan}


@router.post("/learning-plan/{plan_id}/generate-days/{month_index}")
def generate_days_for_month(plan_id: int, month_index: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")

    month = months[month_index - 1]
    # Always regenerate days to guarantee 30 saved days (idempotent overwrite)
    onboarding = db.query(Onboarding).filter(Onboarding.user_id == plan.user_id).first()
    if not onboarding:
        raise HTTPException(status_code=400, detail="Onboarding data required")
    month["days"] = _generate_days_for_month_via_ai(month, onboarding)
    months[month_index - 1] = month
    plan.plan = {"months": [dict(m) for m in months]}
    db.commit()
    db.refresh(plan)
    return {"message": "Days generated", "plan": plan.plan}


def _generate_day_detail_via_ai(month: dict, day: dict, onboarding: Onboarding) -> dict:
    import json
    try:
        prompt = f"""
Generate a comprehensive, detailed study plan for this specific day as pure JSON.

Month Title: {month.get('title')}
Month Description: {month.get('description', '')}
Day: {day.get('day')}
Concept: {day.get('concept')}
Time Estimate: {day.get('time_estimate', 60)} minutes
Daily Time Commitment: {onboarding.time_commitment}
Learner Profile:
- Grade/Level: {onboarding.grade}
- Career Goals: {onboarding.career_goals}
- Current Skills: {onboarding.current_skills}

Rules:
- Output strictly valid JSON with keys: overview, sections, resources, checklist, learning_objectives.
- overview: comprehensive description of what will be learned today
- sections: list of study sections with {{ title, minutes, steps: [detailed steps], focus_areas: [specific topics] }}
- resources: list of {{ type, title, url?, description }}
- checklist: list of concrete tasks to complete
- learning_objectives: list of specific things the learner should understand by end of day
- Total time should match the day's time_estimate
- Make content specific, actionable, and aligned with the concept
- Include practical examples and exercises where appropriate
- No markdown, no extra text, only JSON.
"""
        ai = chatbot.model
        raw = ai.generate_content(prompt)
        text = raw.text
        try:
            return json.loads(text)
        except Exception:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
    except Exception:
        # Comprehensive fallback
        return {
            "overview": f"Comprehensive study session focused on {day.get('concept')}",
            "sections": [
                {"title": "Theory and Concepts", "minutes": 25, "steps": ["Read core concepts", "Take detailed notes", "Identify key principles"], "focus_areas": ["Fundamentals", "Core theory"]},
                {"title": "Practical Application", "minutes": 25, "steps": ["Work through examples", "Practice problems", "Apply concepts"], "focus_areas": ["Hands-on practice", "Problem solving"]},
                {"title": "Review and Assessment", "minutes": 10, "steps": ["Summarize learning", "Self-assessment", "Prepare for quiz"], "focus_areas": ["Consolidation", "Understanding check"]}
            ],
            "resources": [
                {"type": "documentation", "title": "Core Concepts Guide", "description": "Essential reading for today's topic"}
            ],
            "checklist": ["Complete theory reading", "Finish practice exercises", "Review key concepts", "Prepare for assessment"],
            "learning_objectives": ["Understand core concepts", "Apply knowledge practically", "Demonstrate comprehension"]
        }


@router.post("/learning-plan/{plan_id}/month/{month_index}/day/{day}/start")
def start_day(plan_id: int, month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == int(user_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or unauthorized access")

    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")

    month = months[month_index - 1]
    days = month.get("days", [])
    
    if day < 1 or day > len(days):
        raise HTTPException(status_code=400, detail="Invalid day")

    # Check if previous day is completed (enforce sequential progression)
    if day > 1 and not days[day - 2].get("completed"):
        # Auto-heal: if the user passed the previous day's quiz, mark previous day as completed
        try:
            from app.models.quiz import QuizSubmission
            passed_prev = db.query(QuizSubmission).filter(
                QuizSubmission.user_id == int(user_id),
                QuizSubmission.plan_id == plan_id,
                QuizSubmission.month_index == month_index,
                QuizSubmission.day == day - 1,
                QuizSubmission.passed == 1
            ).order_by(QuizSubmission.created_at.desc()).first()
            if passed_prev:
                days[day - 2]["completed"] = True
                days[day - 2]["quiz_score"] = passed_prev.score
                days[day - 2]["completed_at"] = datetime.utcnow().isoformat()
                month["days"] = days
                months[month_index - 1] = month
                plan.plan = {"months": months}
                db.commit()
            else:
                raise HTTPException(status_code=400, detail="Complete previous day first")
        except HTTPException:
            raise
        except Exception as e:
            print(f"Auto-heal check failed for previous day completion: {str(e)}")
            raise HTTPException(status_code=400, detail="Complete previous day first")

    # Generate day detail if not present
    if not days[day - 1].get("detail"):
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
            if onboarding:
                days[day - 1]["detail"] = _generate_day_detail_via_ai(month, days[day - 1], onboarding)
            else:
                # Fallback detail if no onboarding data
                days[day - 1]["detail"] = {
                    "overview": f"Study session focused on {days[day - 1].get('concept')}",
                    "sections": [
                        {"title": "Core Learning", "minutes": days[day - 1].get('time_estimate', 60), "steps": ["Study the material", "Take notes", "Practice"], "focus_areas": ["Key concepts"]}
                    ],
                    "resources": [],
                    "checklist": ["Complete the study session", "Take the quiz"],
                    "learning_objectives": ["Understand the core concepts"]
                }
        except Exception as e:
            print(f"Error generating day detail: {str(e)}")
            # Fallback detail
            days[day - 1]["detail"] = {
                "overview": f"Study session focused on {days[day - 1].get('concept')}",
                "sections": [
                    {"title": "Core Learning", "minutes": days[day - 1].get('time_estimate', 60), "steps": ["Study the material", "Take notes", "Practice"], "focus_areas": ["Key concepts"]}
                ],
                "resources": [],
                "checklist": ["Complete the study session", "Take the quiz"],
                "learning_objectives": ["Understand the core concepts"]
            }

    # Mark day as started
    days[day - 1]["started_at"] = datetime.utcnow().isoformat()
    
    # Ensure quiz exists for this day; auto-generate if missing so it appears in quizzes section
    try:
        from app.models.quiz import Quiz
        from app.models.onboarding import Onboarding as _Onb
        from app.routes.quiz import _generate_quiz_via_ai as _gen_quiz
        existing_quiz = db.query(Quiz).filter(
            Quiz.plan_id == plan.id,
            Quiz.month_index == month_index,
            Quiz.day == day,
            Quiz.user_id == int(user_id)
        ).order_by(Quiz.id.desc()).first()
        if not days[day - 1].get("quiz_id") and not existing_quiz:
            _onb = db.query(_Onb).filter(_Onb.user_id == int(user_id)).first()
            if _onb:
                questions = _gen_quiz(month, days[day - 1], _onb, 10)
                quiz = Quiz(
                    user_id=int(user_id),
                    plan_id=plan.id,
                    month_index=month_index,
                    day=day,
                    title=f"Day {day} Quiz - {days[day - 1].get('concept', 'Learning Assessment')}",
                    questions=questions,
                    required_score=days[day - 1].get("quiz_min_score", 70)
                )
                db.add(quiz)
                db.commit()
                db.refresh(quiz)
                days[day - 1]["quiz_id"] = quiz.id
    except Exception as _qe:
        print(f"Auto-generate quiz failed for day {day}: {_qe}")

    # Update the plan in database
    month["days"] = days
    months[month_index - 1] = month
    plan.plan = {"months": months}
    
    # Update LearningPath current day
    learning_path = db.query(LearningPath).filter(
        LearningPath.plan_id == plan_id,
        LearningPath.global_month_index == month_index
    ).first()
    
    if learning_path:
        learning_path.current_day = day
        learning_path.last_activity_at = datetime.utcnow()
    
    # Update user's current position
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user:
        user.current_day = day
    
    # Google Drive: create a notes file for this day in month folder
    try:
        from app.core.google_services import ensure_drive_folder, create_drive_file, create_calendar_event
        root_name = f"EDUAI_{(user.google_name or user.email or 'USER').split(' ')[0]}_LEARNING_MAIN_PATH" if user else "EDUAI_USER_LEARNING_MAIN_PATH"
        root_id = ensure_drive_folder(int(user_id), root_name)
        month_id = ensure_drive_folder(int(user_id), f"MONTH_{month_index}", parent_id=root_id) if root_id else None
        if month_id:
            day_detail = days[day - 1].get('detail') or {}
            overview = day_detail.get('overview', '')
            sections = day_detail.get('sections', [])
            content_lines = [
                f"Day {day} - {days[day - 1].get('concept','')}",
                "",
                "Overview:",
                overview,
                "",
                "Sections:" 
            ]
            for s in sections:
                content_lines.append(f"- {s.get('title','')} ({s.get('minutes',0)} min)")
                steps = s.get('steps') or []
                for st in steps:
                    content_lines.append(f"  * {st}")
            create_drive_file(int(user_id), f"DAY_{day}_NOTES.txt", "\n".join(content_lines), parent_id=month_id)
        # Optional calendar entry for immediate next hour based on time_estimate
        try:
            minutes = int(days[day - 1].get('time_estimate', 60))
            create_calendar_event(int(user_id), f"Study: Day {day}", datetime.utcnow(), duration_minutes=minutes, description=days[day - 1].get('concept',''))
        except Exception:
            pass
    except Exception as gerr:
        print(f"Drive/Calendar day assets error: {gerr}")
    
    db.commit()
    db.refresh(plan)
    
    return {
        "message": f"Day {day} started successfully",
        "day": days[day - 1],
        "plan": plan.plan
    }


@router.post("/learning-plan/{plan_id}/complete-day/{month_index}/{day}")
def complete_day(plan_id: int, month_index: int, day: int, score: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    # Verify user from token
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user for updating current position
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get plan and verify it belongs to the user
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == int(user_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or unauthorized access")

    months = plan.plan.get("months", [])
    if month_index < 1 or month_index > len(months):
        raise HTTPException(status_code=400, detail="Invalid month index")

    month = months[month_index - 1]
    days = month.get("days", [])
    if day < 1 or day > len(days):
        raise HTTPException(status_code=400, detail="Invalid day")

    # Enforce sequential progression
    if day > 1 and not days[day - 2].get("completed"):
        raise HTTPException(status_code=400, detail="Complete previous day first")
    
    # Verify that a quiz exists for this day
    from app.models.quiz import Quiz
    quiz = db.query(Quiz).filter(
        Quiz.plan_id == plan_id,
        Quiz.month_index == month_index,
        Quiz.day == day,
        Quiz.user_id == int(user_id)
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=400, detail="You must generate a quiz before completing this day")

    # Enforce minimum quiz score
    required = days[day - 1].get("quiz_min_score", 70)
    if score < required:
        # Always save the score even if it's not passing
        days[day - 1]["quiz_score"] = score
        days[day - 1]["quiz_attempts"] = days[day - 1].get("quiz_attempts", 0) + 1
        
        # If multiple failed attempts, regenerate day content to help user
        if days[day - 1]["quiz_attempts"] >= 2:
            try:
                # Get onboarding data for personalized day detail regeneration
                onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
                if onboarding:
                    # Regenerate day detail with more focus on areas user is struggling with
                    day_detail = _generate_day_detail_via_ai(month, days[day - 1], onboarding)
                    days[day - 1]["detail"] = day_detail
                    days[day - 1]["regenerated_at"] = datetime.utcnow().isoformat()
                    days[day - 1]["regenerated_after_attempts"] = days[day - 1]["quiz_attempts"]
            except Exception as e:
                print(f"Error regenerating day detail after failed attempts: {str(e)}")
        
        month["days"] = days
        # Update the plan to save the attempt
        plan.plan = {"months": [dict(m) for m in months]}
        db.commit()
        
        # Determine message based on attempts
        if days[day - 1]["quiz_attempts"] >= 2:
            message = f"Minimum score {required}% required to proceed. Your score: {score}%. The day's content has been refreshed with additional explanations to help you understand the material better. Please review and try again."
        else:
            message = f"Minimum score {required}% required to proceed. Your score: {score}%. Please review the material and try again."
            
        raise HTTPException(status_code=400, detail=message)

    # Save the score in the day data for reference
    days[day - 1]["quiz_score"] = score
    days[day - 1]["quiz_attempts"] = days[day - 1].get("quiz_attempts", 0) + 1
    days[day - 1]["completed"] = True
    days[day - 1]["completed_at"] = datetime.utcnow().isoformat()
    month["days"] = days
    
    # Log completion for debugging
    print(f"Day {day} in month {month_index} marked as completed with score {score}%")
    
    # Send email notification for quiz completion
    try:
        # Check if user has Google account connected (required for email sending)
        if user.google_id and user.email:
            # Prepare context for email notification
            quiz_title = days[day - 1].get("concept", "Quiz")
            email_context = {
                "score": score,
                "passed": score >= required,
                "title": quiz_title,
                "month_index": month_index,
                "day": day
            }
            # Send the email notification asynchronously (don't wait for result)
            # We don't want to block the API response if email sending fails
            threading.Thread(
                target=send_notification_email,
                args=(int(user_id), "quiz_completion", email_context)
            ).start()
    except Exception as e:
        # Log error but don't fail the API call
        print(f"Error sending quiz completion email: {str(e)}")

    # If all days complete, mark month complete and auto-start next month
    if all(d.get("completed") for d in days):
        month["status"] = "completed"
        month["completed_at"] = datetime.utcnow().isoformat()
        
        # Mark path complete
        current_path = db.query(LearningPath).filter(LearningPath.plan_id == plan.id, LearningPath.global_month_index == month_index).first()
        if current_path:
            current_path.status = "completed"
            current_path.completed_at = datetime.utcnow()
            
        # Send learning progress notification
        try:
            if user.google_id and user.email:
                # Calculate overall progress
                total_months = len(months)
                completed_months = sum(1 for m in months if m.get("status") == "completed")
                
                # Count total days and completed days across all months
                total_days = sum(len(m.get("days", [])) for m in months)
                completed_days = sum(sum(1 for d in m.get("days", []) if d.get("completed")) for m in months)
                
                # Calculate progress percentage
                progress_percentage = int((completed_days / total_days * 100) if total_days > 0 else 0)
                
                # Prepare context for email notification
                email_context = {
                    "month_index": month_index,
                    "day": day,
                    "days_completed": completed_days,
                    "total_days": total_days,
                    "progress_percentage": progress_percentage
                }
                
                # Send the email notification asynchronously
                threading.Thread(
                    target=send_notification_email,
                    args=(int(user_id), "learning_progress", email_context)
                ).start()
        except Exception as e:
            # Log error but don't fail the API call
            print(f"Error sending learning progress email: {str(e)}")
            
        # Find next month to activate - always activate the next uncompleted month
        next_month_activated = False
        for i in range(len(months)):
            # Skip current month and already completed months
            if i == (month_index - 1) or months[i].get("status") == "completed":
                continue
                
            # Lock all months after the next uncompleted month
            if next_month_activated:
                months[i]["status"] = "locked"
                continue
                
            # This is the next uncompleted month - activate it
            next_month = months[i]
            
            # Generate days for next month if not already generated
            if not next_month.get("days") or len(next_month.get("days", [])) == 0:
                onboarding = db.query(Onboarding).filter(Onboarding.user_id == plan.user_id).first()
                if onboarding:
                    next_month["days"] = _generate_days_for_month_via_ai(next_month, onboarding)
                    next_month["days_generated"] = True
            
            # Activate next month
            next_month["status"] = "active"
            next_month["started_at"] = datetime.utcnow().isoformat()
            next_month_activated = True
            
            # Update LearningPath for next active month
            next_path = db.query(LearningPath).filter(LearningPath.plan_id == plan.id, LearningPath.global_month_index == (i + 1)).first()
            if next_path:
                next_path.status = "active"
                next_path.started_at = datetime.utcnow()
                
                # Lock all subsequent months
                for j in range(i + 1, len(months)):
                    if months[j].get("status") != "completed":
                        months[j]["status"] = "locked"
                
                # Update user's current position to first day of next month
                user.current_month_index = i + 1
                user.current_day = 1
                break
        
        # If we've completed the final month, mark the entire plan as completed
        if all(m.get("status") == "completed" for m in months):
            plan.status = "completed"
            plan.completed_at = datetime.utcnow()
            print(f"Learning plan {plan.id} for user {plan.user_id} has been completed!")
    else:
        # Find the next incomplete day in this month
        next_day = None
        for i, d in enumerate(days, start=1):
            if not d.get("completed", False):
                next_day = i
                break
        
        # Update user's current position to next incomplete day
        if next_day:
            user.current_month_index = month_index
            user.current_day = next_day

    months[month_index - 1] = month
    plan.plan = {"months": [dict(m) for m in months]}
    db.commit()
    db.refresh(plan)
    return {"message": "Day completed", "plan": plan.plan}


@router.get("/learning-plan", response_model=LearningPlanResponse)
def get_learning_plan(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    plan = db.query(LearningPlan).filter(LearningPlan.user_id == int(user_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Learning plan not found")
    
    # Always fetch fresh data from database and ensure days_generated tracking
    months = plan.plan.get("months", []) if isinstance(plan.plan, dict) else []
    updated = False
    
    for i, m in enumerate(months):
        # Check if days are generated for active months
        if m.get("status") == "active" and (not m.get("days_generated") or not m.get("days") or len(m.get("days", [])) == 0):
            onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
            if onboarding:
                m["days"] = _generate_days_for_month_via_ai(m, onboarding)
                m["days_generated"] = True
                months[i] = m
                updated = True
        # Ensure days_generated flag exists for all months
        elif "days_generated" not in m:
            m["days_generated"] = bool(m.get("days") and len(m.get("days", [])) > 0)
            months[i] = m
            updated = True
        # If days_generated is True but days are empty, regenerate them
        elif m.get("days_generated") and (not m.get("days") or len(m.get("days", [])) == 0):
            onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
            if onboarding:
                m["days"] = _generate_days_for_month_via_ai(m, onboarding)
                months[i] = m
                updated = True
    
    if updated:
        plan.plan = {"months": months}
        db.commit()
        db.refresh(plan)
    
    # Get user's current position
    user = db.query(User).filter(User.id == int(user_id)).first()
    current_position = {
        "current_plan_id": user.current_plan_id,
        "current_month_index": user.current_month_index,
        "current_day": user.current_day
    } if user else None
    
    response = LearningPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        title=plan.title,
        total_years=plan.total_years,
        plan=plan.plan
    )
    
    # Add current position to response
    response_dict = response.dict()
    response_dict["current_position"] = current_position
    
    return response_dict


@router.get("/learning-plan/{plan_id}", response_model=LearningPlanResponse)
def get_learning_plan_by_id(plan_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == int(user_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Learning plan not found")
    months = plan.plan.get("months", []) if isinstance(plan.plan, dict) else []
    updated = False
    for i, m in enumerate(months):
        # Check if days are generated for active months
        if m.get("status") == "active" and (not m.get("days_generated") or not m.get("days") or len(m.get("days", [])) == 0):
            onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
            if onboarding:
                m["days"] = _generate_days_for_month_via_ai(m, onboarding)
                m["days_generated"] = True
                months[i] = m
                updated = True
        # Ensure days_generated flag exists for all months
        elif "days_generated" not in m:
            m["days_generated"] = bool(m.get("days") and len(m.get("days", [])) > 0)
            months[i] = m
            updated = True
        # If days_generated is True but days are empty, regenerate them
        elif m.get("days_generated") and (not m.get("days") or len(m.get("days", [])) == 0):
            onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
            if onboarding:
                m["days"] = _generate_days_for_month_via_ai(m, onboarding)
                months[i] = m
                updated = True
    if updated:
        plan.plan = {"months": months}
        db.commit()
        db.refresh(plan)
    
    # Get user's current position
    user = db.query(User).filter(User.id == int(user_id)).first()
    current_position = {
        "current_plan_id": user.current_plan_id,
        "current_month_index": user.current_month_index,
        "current_day": user.current_day
    } if user else None
    
    response = LearningPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        title=plan.title,
        total_years=plan.total_years,
        plan=plan.plan
    )
    
    # Add current position to response
    response_dict = response.dict()
    response_dict["current_position"] = current_position
    
    return response_dict

