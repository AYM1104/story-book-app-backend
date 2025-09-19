from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, true, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class UploadImage(Base):
    __tablename__ = "upload_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)    
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    meta_json = Column(Text, nullable=True)  # Vision API 解析結果を JSON で保存

    user = relationship("User", backref="upload_images", lazy="joined")
    