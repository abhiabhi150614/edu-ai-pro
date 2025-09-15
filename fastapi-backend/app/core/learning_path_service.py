from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.learning_path import LearningPath, DayProgress
from app.models.learning_plan import LearningPlan
from app.models.user import User


class LearningPathService:
    """Service for managing learning path progression and day advancement"""
    
    @staticmethod
    def get_or_create_day_progress(
        db: Session, 
        user_id: int, 
        plan_id: int, 
        month_index: int, 
        day_number: int
    ) -> DayProgress:
        """Get or create day progress tracking for a specific day"""
        day_progress = db.query(DayProgress).filter(
            DayProgress.user_id == user_id,
            DayProgress.plan_id == plan_id,
            DayProgress.month_index == month_index,
            DayProgress.day_number == day_number
        ).first()
        
        if not day_progress:
            day_progress = DayProgress(
                user_id=user_id,
                plan_id=plan_id,
                month_index=month_index,
                day_number=day_number,
                status="locked"
            )
            db.add(day_progress)
            db.commit()
            db.refresh(day_progress)
        
        return day_progress
    
    @staticmethod
    def start_day(
        db: Session, 
        user_id: int, 
        plan_id: int, 
        month_index: int, 
        day_number: int
    ) -> DayProgress:
        """Mark a day as started and update user's current position"""
        # Get or create day progress
        day_progress = LearningPathService.get_or_create_day_progress(
            db, user_id, plan_id, month_index, day_number
        )
        
        # Update day status
        day_progress.status = "active"
        day_progress.started_at = datetime.utcnow()
        day_progress.content_viewed = True
        
        # Update user's current position
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.current_plan_id = plan_id
            user.current_month_index = month_index
            user.current_day = day_number
        
        # Update learning path tracking
        learning_path = db.query(LearningPath).filter(
            LearningPath.plan_id == plan_id,
            LearningPath.global_month_index == month_index
        ).first()
        
        if learning_path:
            learning_path.current_day = day_number
            learning_path.last_activity_at = datetime.utcnow()
            learning_path.status = "active"
            
            # Initialize days_data if not exists
            if not learning_path.days_data:
                learning_path.days_data = {}
            
            # Update day status in days_data
            learning_path.days_data[str(day_number)] = {
                "status": "active",
                "started_at": datetime.utcnow().isoformat()
            }
        
        db.commit()
        db.refresh(day_progress)
        return day_progress
    
    @staticmethod
    def complete_day(
        db: Session, 
        user_id: int, 
        plan_id: int, 
        month_index: int, 
        day_number: int, 
        quiz_score: int
    ) -> Dict[str, Any]:
        """Complete a day and determine next steps"""
        # Get day progress (create if missing to be robust)
        day_progress = db.query(DayProgress).filter(
            DayProgress.user_id == user_id,
            DayProgress.plan_id == plan_id,
            DayProgress.month_index == month_index,
            DayProgress.day_number == day_number
        ).first()
        if not day_progress:
            day_progress = LearningPathService.get_or_create_day_progress(
                db, user_id, plan_id, month_index, day_number
            )
        
        # Update day completion
        day_progress.status = "completed"
        day_progress.completed_at = datetime.utcnow()
        day_progress.quiz_score = quiz_score
        day_progress.quiz_attempts += 1
        day_progress.can_proceed = True
        
        # Update best score
        if not day_progress.best_score or quiz_score > day_progress.best_score:
            day_progress.best_score = quiz_score
        
        # Update learning path aggregate
        learning_path = db.query(LearningPath).filter(
            LearningPath.plan_id == plan_id,
            LearningPath.global_month_index == month_index
        ).first()
        
        if learning_path:
            learning_path.days_completed += 1
            learning_path.last_activity_at = datetime.utcnow()
            
            # Update days_data
            if not learning_path.days_data:
                learning_path.days_data = {}
            
            learning_path.days_data[str(day_number)] = {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "quiz_score": quiz_score,
                "best_score": day_progress.best_score
            }
            
            # Check if month is completed
            if learning_path.days_completed >= learning_path.total_days:
                learning_path.status = "completed"
                learning_path.completed_at = datetime.utcnow()

        # Also update plan JSON structure to reflect completion for UI
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
        if plan and plan.plan and isinstance(plan.plan, dict) and "months" in plan.plan:
            months = plan.plan.get("months", [])
            if 1 <= month_index <= len(months):
                month = months[month_index - 1]
                days = month.get("days", [])
                if 1 <= day_number <= len(days):
                    # Mark day as completed and store quiz score meta
                    days[day_number - 1]["completed"] = True
                    days[day_number - 1]["quiz_score"] = quiz_score
                    days[day_number - 1]["completed_at"] = datetime.utcnow().isoformat()
                    # Optionally unlock next day implicitly by having previous completed
                    month["days"] = days
                    months[month_index - 1] = month
                    plan.plan = {"months": [dict(m) for m in months]}
        
        # Determine next day
        next_day_info = LearningPathService._get_next_day_info(
            db, plan_id, month_index, day_number
        )
        
        # Update user's current position to next day
        user = db.query(User).filter(User.id == user_id).first()
        if user and next_day_info:
            user.current_day = next_day_info["day_number"]
            if next_day_info["month_index"] != month_index:
                user.current_month_index = next_day_info["month_index"]
        
        db.commit()
        
        return {
            "day_completed": True,
            "next_day": next_day_info,
            "month_completed": learning_path.status == "completed" if learning_path else False
        }
    
    @staticmethod
    def _get_next_day_info(
        db: Session, 
        plan_id: int, 
        month_index: int, 
        day_number: int
    ) -> Optional[Dict[str, Any]]:
        """Get information about the next day to work on"""
        # Check if there's a next day in the same month
        if day_number < 30:
            return {
                "month_index": month_index,
                "day_number": day_number + 1,
                "type": "next_day"
            }
        
        # Check if there's a next month
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
        if not plan or not plan.plan or "months" not in plan.plan:
            return None
        
        months = plan.plan["months"]
        if month_index < len(months):
            next_month = months[month_index]
            if next_month.get("status") == "locked":
                return {
                    "month_index": month_index + 1,
                    "day_number": 1,
                    "type": "next_month_locked"
                }
            else:
                return {
                    "month_index": month_index + 1,
                    "day_number": 1,
                    "type": "next_month_active"
                }
        
        return None
    
    @staticmethod
    def get_user_progress_summary(
        db: Session, 
        user_id: int, 
        plan_id: int
    ) -> Dict[str, Any]:
        """Get a summary of user's progress across all months and days"""
        # Get all day progress for this plan
        day_progress_list = db.query(DayProgress).filter(
            DayProgress.user_id == user_id,
            DayProgress.plan_id == plan_id
        ).all()
        
        # Group by month
        month_progress = {}
        total_days_completed = 0
        total_days_started = 0
        
        for progress in day_progress_list:
            month_idx = progress.month_index
            if month_idx not in month_progress:
                month_progress[month_idx] = {
                    "days_completed": 0,
                    "days_started": 0,
                    "total_days": 30,
                    "best_scores": []
                }
            
            if progress.status == "completed":
                month_progress[month_idx]["days_completed"] += 1
                total_days_completed += 1
                if progress.best_score:
                    month_progress[month_idx]["best_scores"].append(progress.best_score)
            
            if progress.status in ["active", "completed"]:
                month_progress[month_idx]["days_started"] += 1
                total_days_started += 1
        
        # Calculate overall progress
        total_possible_days = len(month_progress) * 30
        overall_progress = (total_days_completed / total_possible_days * 100) if total_possible_days > 0 else 0
        
        return {
            "total_days_completed": total_days_completed,
            "total_days_started": total_days_started,
            "total_possible_days": total_possible_days,
            "overall_progress_percentage": round(overall_progress, 1),
            "month_progress": month_progress,
            "current_position": {
                "plan_id": plan_id,
                "months_with_progress": len(month_progress)
            }
        }
