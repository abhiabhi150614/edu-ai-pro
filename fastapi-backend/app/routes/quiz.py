from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.db import get_db
from app.core.security import decode_token
from app.models.quiz import Quiz, QuizSubmission
from app.models.learning_plan import LearningPlan
from app.models.onboarding import Onboarding
from app.core.gemini_ai import chatbot
from app.routes.learning_plan import _generate_days_for_month_via_ai
from app.core.learning_path_service import LearningPathService

router = APIRouter()
bearer_scheme = HTTPBearer()


def _generate_quiz_via_ai(month: dict, day: dict, onboarding: Onboarding, num_questions: int = 15, problem_areas: list = None) -> List[Dict[str, Any]]:
    import json
    
    def _fallback_quiz(concept="Learning Assessment") -> List[Dict[str, Any]]:
        return [
            {
                "question": f"What is the main focus of today's learning: {concept}?",
                "options": [
                    f"Understanding {concept}",
                    "Memorizing facts",
                    "Taking notes",
                    "None of the above"
                ],
                "correct_index": 0,
                "explanation": f"The main focus is understanding {concept} thoroughly."
            },
            {
                "question": f"Which approach is best for learning {concept}?",
                "options": [
                    "Active practice and application",
                    "Passive reading only",
                    "Skipping difficult parts",
                    "Rushing through quickly"
                ],
                "correct_index": 0,
                "explanation": "Active practice and application is the most effective learning method."
            },
            {
                "question": f"When studying {concept}, what should you do first?",
                "options": [
                    "Understand the fundamentals",
                    "Jump to advanced topics",
                    "Skip the basics",
                    "Memorize without understanding"
                ],
                "correct_index": 0,
                "explanation": "Always start with understanding the fundamentals."
            }
        ]

    try:
        # Build comprehensive prompt for quiz generation
        problem_areas_text = ""
        if problem_areas and len(problem_areas) > 0:
            problem_areas_text = "\nProblem Areas (focus on these):\n" + "\n".join([f"- {area}" for area in problem_areas if area]) + "\n\nIMPORTANT: Generate at least 60% of questions that specifically address these problem areas. Make these questions more detailed and include thorough explanations to help the learner understand these concepts better."
            
        prompt = f"""
Generate a comprehensive multiple-choice quiz as pure JSON for this specific learning day.

CONTEXT:
Month Title: {month.get('title')}
Month Description: {month.get('description', '')}
Day: {day.get('day')}
Learning Concept: {day.get('concept')}
Time Estimate: {day.get('time_estimate', 60)} minutes
Daily Time Commitment: {onboarding.time_commitment}

Learner Profile:
- Grade/Level: {onboarding.grade}
- Career Goals: {onboarding.career_goals}
- Current Skills: {onboarding.current_skills}

Day Detail (if available):
{json.dumps(day.get('detail', {}), indent=2)[:1500]}{problem_areas_text}

REQUIREMENTS:
1) Output strictly valid JSON with key "questions" = array of exactly {num_questions} items.
2) Each question item: {{"question": <string>, "options": [4 options], "correct_index": <0-3>, "explanation": <string>}}
3) Question types should include:
   - Understanding of core concepts (40%)
   - Application and problem-solving (30%)
   - Critical thinking and analysis (20%)
   - Practical implementation (10%)
4) Questions MUST be highly specific to this day's concept and learning objectives:
   - Questions MUST test knowledge from the ACTUAL CONTENT in the day's detail
   - Questions MUST NOT be generic or applicable to any topic
   - Questions MUST focus on the specific learning concept for this day
   - Questions MUST require actual understanding rather than just memorization
   - Questions MUST include specific terminology, examples, and scenarios from the day's content
   - Questions MUST be challenging enough to verify real comprehension
   - Questions MUST test application of knowledge, not just recall
   - Questions MUST have plausible distractors that test common misconceptions
   - Questions MUST cover the most important aspects of the day's learning material
   - Questions MUST include specific terminology, examples, and scenarios from the day's content
   - Questions MUST be challenging enough to verify comprehension but not overly complex
   - Questions MUST test understanding of key principles and terminology introduced in this day
5) Make questions challenging but fair for the learner's level
6) Include detailed explanations that help reinforce learning
7) Ensure all options are plausible but only one is clearly correct
8) Questions MUST require actual understanding of the material, not just memorization
8) Questions should align with the day's concept and learning objectives

Return only JSON, no markdown or extra text.
"""

        ai = chatbot.model
        raw = ai.generate_content(prompt)
        text = raw.text
        
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "questions" in data:
                questions = data["questions"]
            elif isinstance(data, list):
                questions = data
            else:
                return _fallback_quiz()
                
            # Validate and normalize questions
            normalized_questions = []
            for i, q in enumerate(questions[:num_questions]):
                if not isinstance(q, dict):
                    continue
                    
                options = q.get("options", [])
                if len(options) != 4:
                    continue
                    
                correct_index = q.get("correct_index", 0)
                if not isinstance(correct_index, int) or correct_index < 0 or correct_index > 3:
                    correct_index = 0
                    
                normalized_questions.append({
                    "question": q.get("question", f"Question {i+1}"),
                    "options": options,
                    "correct_index": correct_index,
                    "explanation": q.get("explanation", "Review the concept to understand the correct answer.")
                })
            
            # Ensure we have enough questions
            while len(normalized_questions) < num_questions:
                fallback = _fallback_quiz()
                normalized_questions.extend(fallback[:num_questions - len(normalized_questions)])
                
            return normalized_questions[:num_questions]
            
        except Exception:
            # Try to extract JSON if extra text is present
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
            return _fallback_quiz()
            
    except Exception:
        return _fallback_quiz()


@router.post("/quiz/{plan_id}/{month_index}/{day}/generate")
def generate_quiz(plan_id: int, month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
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
    
    # Ensure days are generated for this month
    if not month.get("days") or len(month.get("days", [])) == 0:
        onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
        if not onboarding:
            raise HTTPException(status_code=400, detail="Onboarding data required")
        month["days"] = _generate_days_for_month_via_ai(month, onboarding)
        month["days_generated"] = True
        months[month_index - 1] = month
        plan.plan = {"months": [dict(m) for m in months]}
        db.commit()
        db.refresh(plan)
    
    days = month.get("days", [])
    if day < 1 or day > len(days):
        raise HTTPException(status_code=400, detail="Invalid day")

    # Get onboarding data for personalized quiz generation
    onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
    if not onboarding:
        raise HTTPException(status_code=400, detail="Onboarding data required")
    
    # Ensure day detail is generated if missing
    day_data = days[day - 1]
    if not day_data.get('detail') or not day_data['detail']:
        try:
            # Import the function to generate day detail
            from app.routes.learning_plan import _generate_day_detail_via_ai
            day_detail = _generate_day_detail_via_ai(month, day_data, onboarding)
            day_data['detail'] = day_detail
            days[day - 1] = day_data
            month['days'] = days
            months[month_index - 1] = month
            plan.plan = {"months": [dict(m) for m in months]}
            db.commit()
        except Exception as e:
            print(f"Error generating day detail: {str(e)}")

    # Generate quiz using AI with fallback
    questions = []
    try:
        questions = _generate_quiz_via_ai(month, days[day - 1], onboarding, 15)
    except Exception as e:
        print(f"Error generating quiz via AI: {str(e)}")
        # Use fallback questions
        concept = days[day - 1].get('concept', 'Learning Assessment')
        questions = _fallback_quiz(concept)

    # Create quiz record
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
    
    # Save quiz_id back to the learning plan
    days[day - 1]["quiz_id"] = quiz.id
    month["days"] = days
    months[month_index - 1] = month
    plan.plan = {"months": [dict(m) for m in months]}
    db.commit()
    
    return {
        "quiz_id": quiz.id, 
        "title": quiz.title, 
        "questions": questions, 
        "required_score": quiz.required_score,
        "total_questions": len(questions),
        "message": "Quiz generated successfully"
    }


@router.get("/quiz/{plan_id}/{month_index}/{day}")
def get_quiz(plan_id: int, month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # First try to find the quiz directly
    quiz = db.query(Quiz).filter(
        Quiz.plan_id == plan_id, 
        Quiz.month_index == month_index, 
        Quiz.day == day, 
        Quiz.user_id == int(user_id)
    ).order_by(Quiz.id.desc()).first()
    
    if not quiz:
        # If quiz not found directly, check if there's a quiz_id in the learning plan
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == int(user_id)).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        months = plan.plan.get("months", [])
        if month_index < 1 or month_index > len(months):
            raise HTTPException(status_code=400, detail="Invalid month index")
            
        month = months[month_index - 1]
        days = month.get("days", [])
        if day < 1 or day > len(days):
            raise HTTPException(status_code=400, detail="Invalid day")
            
        day_data = days[day - 1]
        quiz_id = day_data.get("quiz_id")
        
        if quiz_id:
            # Try to find the quiz by ID
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    if not quiz:
        # If still not found, return a 404 with a helpful message
        raise HTTPException(status_code=404, detail="Quiz not found. Generate a quiz first.")
    
    return {
        "quiz_id": quiz.id, 
        "title": quiz.title, 
        "questions": quiz.questions, 
        "required_score": quiz.required_score,
        "total_questions": len(quiz.questions)
    }


@router.post("/quiz/{plan_id}/{month_index}/{day}/submit")
def submit_quiz(plan_id: int, month_index: int, day: int, answers: List[int], credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    quiz = db.query(Quiz).filter(
        Quiz.plan_id == plan_id, 
        Quiz.month_index == month_index, 
        Quiz.day == day, 
        Quiz.user_id == int(user_id)
    ).order_by(Quiz.id.desc()).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Validate answers
    if len(answers) != len(quiz.questions):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match number of questions")

    # Calculate score
    correct = 0
    question_results = []
    
    for i, q in enumerate(quiz.questions):
        user_answer = answers[i] if i < len(answers) else -1
        correct_answer = q.get("correct_index", 0)
        is_correct = user_answer == correct_answer
        
        if is_correct:
            correct += 1
            
        question_results.append({
            "question_index": i,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })
    
    score = int((correct / max(1, len(quiz.questions))) * 100)
    passed = 1 if score >= quiz.required_score else 0

    # Get attempt number for this quiz
    attempt_count = db.query(QuizSubmission).filter(
        QuizSubmission.user_id == int(user_id),
        QuizSubmission.plan_id == plan_id,
        QuizSubmission.month_index == month_index,
        QuizSubmission.day == day
    ).count()
    
    # Record submission with detailed results for analysis
    record = QuizSubmission(
        user_id=int(user_id),
        plan_id=plan_id,
        month_index=month_index,
        day=day,
        quiz_id=quiz.id,
        answers=answers,
        question_results=question_results,  # Store detailed results
        score=score,
        passed=passed,
        attempt_number=attempt_count + 1  # Increment attempt number
    )
    db.add(record)
    db.commit()

    # If quiz is passed, use LearningPathService to complete the day and advance
    if passed:
        try:
            completion_result = LearningPathService.complete_day(
                db, int(user_id), plan_id, month_index, day, score
            )
            
            # Get concept for response
            concept = None
            try:
                plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
                if plan:
                    months = plan.plan.get("months", [])
                    if 1 <= month_index <= len(months):
                        month = months[month_index - 1]
                        days = month.get("days", [])
                        if 1 <= day <= len(days):
                            concept = days[day - 1].get("concept")
            except Exception:
                pass

            return {
                "score": score, 
                "passed": bool(passed), 
                "concept": concept, 
                "title": quiz.title,
                "total_questions": len(quiz.questions),
                "correct_answers": correct,
                "required_score": quiz.required_score,
                "question_results": question_results,
                "day_completed": True,
                "next_day": completion_result.get("next_day"),
                "month_completed": completion_result.get("month_completed", False),
                "message": "Day completed successfully! You can now proceed to the next day."
            }
        except Exception as e:
            print(f"Error completing day via LearningPathService: {str(e)}")
            # Fallback to old behavior if service fails
            pass

    # Get concept for response (fallback)
    concept = None
    try:
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
        if plan:
            months = plan.plan.get("months", [])
            if 1 <= month_index <= len(months):
                month = months[month_index - 1]
                days = month.get("days", [])
                if 1 <= day <= len(days):
                    concept = days[day - 1].get("concept")
    except Exception:
        pass

    return {
        "score": score, 
        "passed": bool(passed), 
        "concept": concept, 
        "title": quiz.title,
        "total_questions": len(quiz.questions),
        "correct_answers": correct,
        "required_score": quiz.required_score,
        "question_results": question_results,
        "day_completed": False,
        "message": f"Quiz not passed. You need {quiz.required_score}% to proceed. Current score: {score}%"
    }


@router.post("/quiz/{plan_id}/{month_index}/{day}/regenerate")
def regenerate_quiz(plan_id: int, month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Regenerate quiz with different questions for retakes"""
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
    days = month.get("days", [])
    if day < 1 or day > len(days):
        raise HTTPException(status_code=400, detail="Invalid day")

    # Get onboarding data
    onboarding = db.query(Onboarding).filter(Onboarding.user_id == int(user_id)).first()
    if not onboarding:
        raise HTTPException(status_code=400, detail="Onboarding data required")
        
    # Get previous quiz attempts to analyze performance
    previous_submissions = db.query(QuizSubmission).filter(
        QuizSubmission.user_id == int(user_id),
        QuizSubmission.plan_id == plan_id,
        QuizSubmission.month_index == month_index,
        QuizSubmission.day == day
    ).order_by(QuizSubmission.created_at.desc()).all()
    
    # Analyze previous submissions to identify problem areas
    problem_areas = []
    question_errors = {}
    
    if previous_submissions:
        # Extract questions that were frequently missed
        for submission in previous_submissions:
            if submission.question_results:
                for result in submission.question_results:
                    if not result.get('is_correct', False):
                        # Get the question text and explanation
                        question = result.get('question', '')
                        explanation = result.get('explanation', '')
                        concept = result.get('concept', '')
                        
                        # Track frequency of missed questions
                        key = question
                        if key not in question_errors:
                            question_errors[key] = {
                                'count': 0,
                                'explanation': explanation,
                                'concept': concept
                            }
                        question_errors[key]['count'] += 1
        
        # Sort by frequency of errors (most frequent first)
        sorted_errors = sorted(question_errors.items(), key=lambda x: x[1]['count'], reverse=True)
        
        # Add the most frequently missed questions' explanations to problem areas
        for question, data in sorted_errors[:5]:  # Focus on top 5 problem areas
            area = f"Concept: {data['concept']}" if data['concept'] else ""
            area += f" - {data['explanation']}" if data['explanation'] else ""
            if area:
                problem_areas.append(area)
    
    # Generate new quiz with focus on problem areas if they exist
    try:
        questions = _generate_quiz_via_ai(month, days[day - 1], onboarding, 15, problem_areas=problem_areas[:3])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate quiz: {str(e)}")

    # Create new quiz record
    quiz = Quiz(
        user_id=int(user_id),
        plan_id=plan.id,
        month_index=month_index,
        day=day,
        title=f"Day {day} Quiz (Retake) - {days[day - 1].get('concept', 'Learning Assessment')}",
        questions=questions,
        required_score=days[day - 1].get("quiz_min_score", 70)
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Update quiz_id in plan
    try:
        months = plan.plan.get("months", [])
        if 1 <= month_index <= len(months):
            month = months[month_index - 1]
            ds = month.get("days", [])
            if 1 <= day <= len(ds):
                ds[day - 1]["quiz_id"] = str(quiz.id)
                month["days"] = ds
                months[month_index - 1] = month
                plan.plan = {"months": months}
                db.commit()
                db.refresh(plan)
    except Exception:
        pass

    # Prepare response message based on problem areas
    message = "New quiz generated for retake"
    if problem_areas:
        message = "New quiz generated with focus on areas that need improvement. This quiz contains questions specifically designed to help you master concepts you found challenging previously."
    
    return {
        "quiz_id": quiz.id, 
        "title": quiz.title, 
        "questions": questions, 
        "required_score": quiz.required_score,
        "total_questions": len(questions),
        "message": message,
        "has_problem_focus": bool(problem_areas)
    }


@router.get("/available-quizzes")
def get_available_quizzes(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get all available quizzes for the current user across all plans"""
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get all quizzes for the user
    quizzes = db.query(Quiz).filter(Quiz.user_id == int(user_id)).order_by(Quiz.created_at.desc()).all()
    
    quiz_list = []
    for quiz in quizzes:
        # Get plan and month info
        plan = db.query(LearningPlan).filter(LearningPlan.id == quiz.plan_id).first()
        if plan and plan.plan and "months" in plan.plan:
            months = plan.plan["months"]
            if 1 <= quiz.month_index <= len(months):
                month = months[quiz.month_index - 1]
                month_title = month.get("title", f"Month {quiz.month_index}")
                
                # Get day info
                days = month.get("days", [])
                if 1 <= quiz.day <= len(days):
                    day_concept = days[quiz.day - 1].get("concept", f"Day {quiz.day}")
                else:
                    day_concept = f"Day {quiz.day}"
                
                # Check if quiz is completed
                submission = db.query(QuizSubmission).filter(
                    QuizSubmission.quiz_id == quiz.id,
                    QuizSubmission.passed == 1
                ).first()
                
                quiz_list.append({
                    "id": quiz.id,
                    "title": quiz.title,
                    "plan_id": quiz.plan_id,
                    "plan_title": plan.title,
                    "month_index": quiz.month_index,
                    "month_title": month_title,
                    "day": quiz.day,
                    "day_concept": day_concept,
                    "required_score": quiz.required_score,
                    "total_questions": len(quiz.questions),
                    "completed": submission is not None,
                    "best_score": submission.score if submission else None,
                    "created_at": quiz.created_at.isoformat(),
                    "url": f"/learning-plans/{quiz.plan_id}/month/{quiz.month_index}/day/{quiz.day}/quiz"
                })
    
    return {
        "quizzes": quiz_list,
        "total_quizzes": len(quiz_list),
        "completed_quizzes": len([q for q in quiz_list if q["completed"]]),
        "pending_quizzes": len([q for q in quiz_list if not q["completed"]])
    }

@router.get("/quiz/{plan_id}/{month_index}/{day}/status")
def get_quiz_status(plan_id: int, month_index: int, day: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    """Get the current status of a quiz for a specific day"""
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if quiz exists
    quiz = db.query(Quiz).filter(
        Quiz.plan_id == plan_id, 
        Quiz.month_index == month_index, 
        Quiz.day == day, 
        Quiz.user_id == int(user_id)
    ).order_by(Quiz.id.desc()).first()
    
    if not quiz:
        return {
            "quiz_exists": False,
            "status": "not_generated",
            "message": "Quiz not yet generated for this day"
        }
    
    # Check if quiz is completed
    submission = db.query(QuizSubmission).filter(
        QuizSubmission.quiz_id == quiz.id,
        QuizSubmission.passed == 1
    ).first()
    
    if submission:
        return {
            "quiz_exists": True,
            "status": "completed",
            "score": submission.score,
            "best_score": submission.score,
            "attempts": submission.attempt_number,
            "completed_at": submission.created_at.isoformat(),
            "message": f"Quiz completed with {submission.score}% score"
        }
    
    # Check if there are failed attempts
    failed_attempts = db.query(QuizSubmission).filter(
        QuizSubmission.quiz_id == quiz.id,
        QuizSubmission.passed == 0
    ).order_by(QuizSubmission.created_at.desc()).all()
    
    if failed_attempts:
        best_score = max([a.score for a in failed_attempts])
        return {
            "quiz_exists": True,
            "status": "failed",
            "best_score": best_score,
            "attempts": len(failed_attempts),
            "last_attempt_score": failed_attempts[0].score,
            "required_score": quiz.required_score,
            "message": f"Quiz failed. Best score: {best_score}%. Required: {quiz.required_score}%"
        }
    
    return {
        "quiz_exists": True,
        "status": "not_attempted",
        "total_questions": len(quiz.questions),
        "required_score": quiz.required_score,
        "message": "Quiz ready to take"
    }


