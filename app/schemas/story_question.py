from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class StoryQuestionBase(BaseModel):
    target_element: str
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    followups: Optional[List[str]] = None
    reason: Optional[str] = None

class StoryQuestionCreate(StoryQuestionBase):
    image_id: int

class StoryQuestion(StoryQuestionBase):
    id: int
    image_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
