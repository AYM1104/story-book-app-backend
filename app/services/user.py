from app.schemas import user as schemas
from app.models import user as models
from sqlalchemy.orm import Session

""" ユーザー作成 """
def create_user(db: Session, user: schemas.UserCreate):
    # ユーザーが存在するか確認
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    # ユーザーが存在する場合はNoneを返す
    if db_user:
        return None
    
    # ユーザーを作成
    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

""" ユーザーログイン """
def login_user(db: Session, user: schemas.UserLogin):
    # ユーザー名またはメールアドレスでユーザーを検索
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if db_user:
        return db_user
    return None

""" ユーザー一覧取得 """
def get_users(db: Session):
    return db.query(models.User).all()
