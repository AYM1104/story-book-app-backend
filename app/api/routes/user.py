from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.schemas import user as schemas
from app.services import user as services

router = APIRouter(prefix="/api/users", tags=["users"])

# DB依存性
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

""" ユーザー作成のエンドポイント """
@router.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.create_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return db_user

""" ユーザーログインのエンドポイント """
@router.post("/login", response_model=schemas.UserResponse)
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = services.login_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid username or email")
    
    return db_user

""" ユーザー一覧取得のエンドポイント """
@router.get("/users", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return services.get_users(db)