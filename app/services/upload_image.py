import os
import shutil
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from pathlib import Path
from app.models.upload_image import UploadImage

class UploadImageService:

    # 初期化
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    # ファイルをアップロード
    def save_image(self, db: Session, *, file, filename: str, content_type: str, public_base: str) -> UploadImage:
        # 拡張子チェック
        lower = filename.lower()
        if not lower.endswith((".png", ".jpg", ".jpeg")):
            raise ValueError("Invalid file type")

        # ユニークファイル名生成
        ext = Path(filename).suffix or ".bin"
        safe_name = f"{uuid4().hex}{ext}"
        dst = self.upload_dir / safe_name

        with open(dst, "wb") as f:
            shutil.copyfileobj(file, f)

        size = dst.stat().st_size
        url = f"{public_base.rstrip('/')}/uploads/{safe_name}"

        # DB保存
        img = UploadImage(
            filename=safe_name,
            url=url,
            content_type=content_type or "application/octet-stream",
            size_bytes=size,
            user_id=None
        )
        db.add(img)
        try:
            db.commit()
            db.refresh(img)
        except SQLAlchemyError:
            db.rollback()
            os.remove(dst)
            raise

        return img

    def list_images(self, db: Session) -> list[UploadImage]:
        return db.query(UploadImage).order_by(UploadImage.uploaded_at.desc()).all()