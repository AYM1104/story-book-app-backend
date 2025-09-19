from pydantic import BaseModel, AnyUrl
from datetime import datetime
from typing import Optional

class UploadImageResponse(BaseModel):
    id: int
    filename: str
    url: AnyUrl | str
    content_type: str
    size_bytes: int
    user_id: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

        