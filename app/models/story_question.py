from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class StoryQuestion(Base):
    """物語作成のための質問"""
    __tablename__ = "story_questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey("upload_images.id"), nullable=False)
    target_element = Column(String(100), nullable=False)  # 主人公、舞台、問題など
    question_text = Column(String(500), nullable=False)
    question_type = Column(String(50), nullable=False)  # open, choice
    options = Column(JSON, nullable=True)  # 選択肢（choice型の場合）
    followups = Column(JSON, nullable=True)  # フォローアップ質問
    reason = Column(String(500), nullable=True)  # 質問の理由
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # リレーション
    image = relationship("UploadImage")
    answers = relationship("StoryAnswer", back_populates="question", cascade="all, delete")
