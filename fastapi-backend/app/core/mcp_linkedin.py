"""
MCP-based LinkedIn Integration for EduAI
Uses third-party services for simplified LinkedIn posting
"""

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.quiz import QuizSubmission
from app.models.learning_plan import LearningPlan
from app.core.learning_path_service import LearningPathService
from app.database.db import get_db
import logging

logger = logging.getLogger(__name__)

class MCPLinkedInService:
    def __init__(self):
        # MCP approach - no external APIs needed
        pass
    
    def generate_learning_post(self, user_id: int, day: int, custom_topic: str = None) -> str:
        """Generate LinkedIn post content"""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            plan = db.query(LearningPlan).filter(LearningPlan.user_id == user_id).first()
            
            if not user or not plan:
                return "🎓 Continuing my learning journey with EduAI! #Learning #AI #Education"
            
            # Get current day concept
            months = plan.plan.get("months", []) if isinstance(plan.plan, dict) else []
            current_concept = "New concepts"
            
            if user.current_month_index <= len(months):
                current_month = months[user.current_month_index - 1]
                days = current_month.get("days", [])
                if day <= len(days):
                    current_day_data = days[day - 1]
                    current_concept = current_day_data.get("concept", "New concepts")
            
            # Get quiz score
            quiz_text = ""
            recent_quiz = db.query(QuizSubmission).filter(
                QuizSubmission.user_id == user_id,
                QuizSubmission.day == day,
                QuizSubmission.month_index == user.current_month_index
            ).order_by(QuizSubmission.created_at.desc()).first()
            
            if recent_quiz:
                quiz_text = f" Quiz Score: {recent_quiz.score}% {'✅' if recent_quiz.passed else '📚'}"
            
            # Get overall progress
            summary = LearningPathService.get_user_progress_summary(db, user_id, plan.id)
            progress_percent = summary.get('overall_progress_percentage', 0)
            
            # Use custom topic if provided
            if custom_topic:
                current_concept = custom_topic
                post_content = f"""🎓 Just learned about {custom_topic}! 

📚 Key Focus: {current_concept}
{quiz_text}
📊 Overall Progress: {progress_percent}%

Amazing how EduAI breaks down complex topics into digestible lessons! 

#Learning #AI #Education #TechSkills #ContinuousLearning #EduAI"""
            else:
                # Generate post content
                post_content = f"""🎓 Day {day} of my {plan.title} learning journey completed! 

📚 Today's Focus: {current_concept}
{quiz_text}
📊 Overall Progress: {progress_percent}%

Loving the structured approach with EduAI - it's making complex topics digestible and engaging! 

#Learning #AI #Education #TechSkills #ContinuousLearning #EduAI"""
            
            return post_content
            
        finally:
            db.close()
    

    
    def generate_shareable_link(self, content: str, user_id: int) -> str:
        """Generate a shareable link for manual posting"""
        # URL encode the content for LinkedIn sharing
        import urllib.parse
        encoded_content = urllib.parse.quote(content)
        
        # LinkedIn share URL
        linkedin_share_url = f"https://www.linkedin.com/sharing/share-offsite/?url=https://eduai.com&text={encoded_content}"
        
        return linkedin_share_url

# Global MCP LinkedIn service instance
mcp_linkedin_service = MCPLinkedInService()

def post_to_linkedin_mcp(user_id: int, day: int, method: str = "link", custom_topic: str = None) -> Dict[str, Any]:
    """Post learning progress to LinkedIn using MCP approach"""
    try:
        # Generate post content
        content = mcp_linkedin_service.generate_learning_post(user_id, day, custom_topic)
        
        # Generate shareable link for manual posting
        share_link = mcp_linkedin_service.generate_shareable_link(content, user_id)
        result = {
            "success": True,
            "method": "manual_link",
            "share_link": share_link,
            "content": content,
            "message": "Click the link to share on LinkedIn"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"MCP LinkedIn posting error: {str(e)}")
        return {"success": False, "error": str(e)}