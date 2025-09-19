from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class StoryAnswerBase(BaseModel):
    answer_text: str
    selected_option: Optional[str] = None
    followup_answers: Optional[Dict[str, str]] = None

class StoryAnswerCreate(StoryAnswerBase):
    question_id: int
    user_id: Optional[int] = None

class StoryAnswer(StoryAnswerBase):
    id: int
    question_id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnswerSubmissionRequest(BaseModel):
    answers: List[StoryAnswerCreate]
