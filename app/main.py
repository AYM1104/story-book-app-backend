import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import user, upload_image, asset_analysis, story
from app.database.session import engine, Base
from app.models import user as user_models
from app.models import upload_image as upload_image_models

app = FastAPI(
    title="Story Book App API",
    description="画像から物語を生成するアプリケーションのAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なドメインを指定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベーステーブル作成（必要に応じて手動実行）
# Base.metadata.create_all(bind=engine)

""" ルーター登録 """
app.include_router(user.router)  # ユーザー関連のルーター
app.include_router(upload_image.router)  # アップロード関連のルーター
app.include_router(asset_analysis.router)  # アセット解析関連のルーター 
app.include_router(story.router)  # 物語生成関連のルーター

""" 静的ファイルの配信 """
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
