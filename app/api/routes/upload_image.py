from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pathlib import Path
from app.database.session import SessionLocal
from app.schemas.upload_image import UploadImageResponse
from app.models.upload_image import UploadImage
from app.services.upload_image import UploadImageService
from app.services.remove_bg import RemoveBgStorage
from sqlalchemy.orm import Session

router = APIRouter()

""" 保存先とサービス初期化 """
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"

# サービス初期化
upload_image_service = UploadImageService(UPLOAD_DIR)
remove_bg_storage = RemoveBgStorage(UPLOAD_DIR)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


""" 画像をアップロードするエンドポイント """
@router.post("/upload", response_model=UploadImageResponse)
async def upload_file(
    request: Request, 
    file: UploadFile = File(...), 
    remove_bg: bool = False,
    db: Session = Depends(get_db)
):
    try:
        # ファイル名の検証
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
        
        base_url = str(request.base_url).rstrip("/")
        
        # 背景削除が有効な場合
        if remove_bg:
            # ファイルを一時的にリセット
            file.file.seek(0)
            # 背景削除して保存
            filename, size = remove_bg_storage.save_with_bg_removed(file.file, file.filename)
            url = f"{base_url}/uploads/{filename}"
            
            # DB保存
            img = UploadImage(
                filename=filename,
                url=url,
                content_type="image/png",  # 背景削除後はPNG
                size_bytes=size,
                user_id=None
            )
            db.add(img)
            db.commit()
            db.refresh(img)
            
            return img
        else:
            # 通常のアップロード
            uploaded_image = upload_image_service.save_image(
                db=db,
                file=file.file,
                filename=file.filename,
                content_type=file.content_type,
                public_base=base_url
            )
            return uploaded_image
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アップロード中にエラーが発生しました: {str(e)}")

""" 画像一覧を取得するエンドポイント """
@router.get("/images", response_model=list[UploadImageResponse])
def list_images(db: Session = Depends(get_db)):
    try:
        return upload_image_service.list_images(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像一覧の取得中にエラーが発生しました: {str(e)}")
