from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class BookPage(Base):
    __tablename__ = "book_pages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    caption = Column(String(1000), nullable=True)
    rendered_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    book = relationship("Book", back_populates="pages")