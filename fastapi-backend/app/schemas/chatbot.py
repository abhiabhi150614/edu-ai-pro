from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    message_id: str

class ChatHistory(BaseModel):
    messages: List[dict]
    user_id: int
