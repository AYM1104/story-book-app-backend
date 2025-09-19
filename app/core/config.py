from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # データベース設定
    database_url: str = "mysql+pymysql://root:password@localhost:3306/story_book_db"
    
    # Google API設定
    google_api_key: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Remove.bg API設定
    remove_bg_api_key: Optional[str] = None
    
    # アプリケーション設定
    secret_key: str = "your-secret-key-here"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 環境変数名のマッピング
        env_prefix = ""  # プレフィックスなし
        case_sensitive = False  # 大文字小文字を区別しない
        extra = "ignore"  # 追加フィールドを無視

settings = Settings()