#!/usr/bin/env python3
"""
データベーステーブル作成スクリプト
"""

from app.database.session import engine, Base
from app.models import user as user_models
from app.models import upload_image as upload_image_models
from app.models.story_question import StoryQuestion
from app.models.story_answer import StoryAnswer

def create_tables():
    """データベーステーブルを作成"""
    try:
        print("データベーステーブルを作成中...")
        Base.metadata.create_all(bind=engine)
        print("✅ データベーステーブルの作成が完了しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    print("データベーステーブルを作成しています...")
    create_tables()
    print("テーブル作成完了!")
