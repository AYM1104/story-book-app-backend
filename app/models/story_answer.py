from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class StoryAnswer(Base):
    """物語作成のための質問への回答"""
    __tablename__ = "story_answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("story_questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    answer_text = Column(Text, nullable=False)
    selected_option = Column(String(200), nullable=True)  # 選択肢型の場合
    followup_answers = Column(JSON, nullable=True)  # フォローアップ回答
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # リレーション
    question = relationship("StoryQuestion", back_populates="answers")
    user = relationship("User")
