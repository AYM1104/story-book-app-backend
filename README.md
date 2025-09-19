# 📚 Story Book App - Backend

物語作成アプリのバックエンドAPIサーバーです。画像アップロード、背景除去、ユーザー管理などの機能を提供します。

## 🚀 機能

- **ユーザー管理** - ユーザー登録・認証
- **画像アップロード** - 画像ファイルのアップロードと管理
- **背景除去** - Google Cloud Vision APIを使用した背景除去機能
- **本とページ管理** - 物語の本とページの作成・管理
- **RESTful API** - FastAPIベースのAPI

## 🛠️ 技術スタック

- **FastAPI** - モダンなPython Webフレームワーク
- **SQLAlchemy** - ORM（Object-Relational Mapping）
- **Pydantic** - データバリデーションとシリアライゼーション
- **MySQL** - データベース（PyMySQLドライバー使用）
- **Google Cloud Vision API** - 画像解析・背景除去
- **Pillow** - 画像処理
- **Uvicorn** - ASGIサーバー

## 📋 必要な環境

- Python 3.12+
- MySQL 8.0+
- Google Cloud Platform アカウント（Vision API用）

## 🔧 セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd story-book-app/backend
```

### 2. 仮想環境の作成とアクティベート

```bash
# 仮想環境作成
python -m venv venv

# 仮想環境アクティベート
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルを作成し、以下の変数を設定してください：

```env
# データベース設定
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/story_book_db

# Google Cloud設定
GOOGLE_APPLICATION_CREDENTIALS=app/secrets/your-service-account-key.json

# その他の設定
SECRET_KEY=your-secret-key
DEBUG=True
```

### 5. データベースのセットアップ

```bash
# データベースマイグレーション（必要に応じて）
# データベーステーブルの作成
```

### 6. サーバーの起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下のURLでAPIにアクセスできます：
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 プロジェクト構成

```
backend/
├── app/
│   ├── api/                 # APIルート
│   │   └── routes/
│   ├── core/                # コア設定
│   ├── database/            # データベース設定
│   ├── models/              # SQLAlchemyモデル
│   ├── schemas/             # Pydanticスキーマ
│   ├── services/            # ビジネスロジック
│   ├── secrets/             # 機密ファイル（Git無視）
│   ├── uploads/             # アップロードファイル
│   └── main.py              # アプリケーションエントリーポイント
├── static/                  # 静的ファイル
├── venv/                    # Python仮想環境
├── requirements.txt         # 依存関係
└── README.md               # このファイル
```

## 🔐 セキュリティ

- `app/secrets/`フォルダは`.gitignore`に含まれており、機密情報はGitにコミットされません
- Google Cloudサービスアカウントキーは安全に管理してください
- 本番環境では適切な環境変数設定を行ってください

## 📝 API エンドポイント

### ユーザー関連
- `POST /api/users/` - ユーザー登録
- `GET /api/users/{user_id}` - ユーザー情報取得

### 画像関連
- `POST /api/upload-image/` - 画像アップロード
- `GET /api/upload-image/{image_id}` - 画像情報取得

### 本・ページ関連
- `POST /api/books/` - 本の作成
- `GET /api/books/{book_id}` - 本の情報取得
- `POST /api/book-pages/` - ページの作成

## 🤝 開発

### コードスタイル
- PEP 8に準拠
- 型ヒントの使用を推奨
- docstringの記述を推奨

### テスト
```bash
# テストの実行（テストファイルがある場合）
pytest
```

## 📄 ライセンス

このプロジェクトのライセンスについては、プロジェクトオーナーにお問い合わせください。

## 🆘 サポート

問題が発生した場合は、以下を確認してください：

1. 仮想環境が正しくアクティベートされているか
2. 必要な環境変数が設定されているか
3. データベース接続が正常か
4. Google Cloud認証情報が正しいか

---

**開発者**: [あなたの名前]  
**最終更新**: 2025年1月