import requests
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
from uuid import uuid4
import os

# .env を読み込む
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")

# 環境変数が設定されていない場合はエラー
if not REMOVE_BG_API_KEY:
    raise RuntimeError(
        "REMOVE_BG_API_KEY が設定されていません。backend/.env に remove.bg の API キーを設定してください"
    )


# 背景を削除して保存するクラス
class RemoveBgStorage:

    # 初期化
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    # 背景を削除して保存
    def save_with_bg_removed(self, file_obj, orig_filename: str) -> tuple[str, int]:
        # APIに送信
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": file_obj},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )

        # ステータスコードが200でない場合はエラー
        if response.status_code != 200:
            raise RuntimeError(f"remove.bg API error: {response.status_code}, {response.text}")

        # 透過PNGで保存
        safe_name = f"{uuid4().hex}.png"
        dst = self.upload_dir / safe_name
        
        print(f"DEBUG: 保存先パス: {dst}")
        print(f"DEBUG: ディレクトリ存在: {self.upload_dir.exists()}")
        print(f"DEBUG: レスポンスサイズ: {len(response.content)}")
        
        try:
            with open(dst, "wb") as out:
                out.write(response.content)
            print(f"DEBUG: ファイル保存成功: {dst}")
        except Exception as e:
            print(f"DEBUG: ファイル保存エラー: {e}")
            raise

        # サイズを取得
        size = dst.stat().st_size
        print(f"DEBUG: 保存されたファイルサイズ: {size}")
        return safe_name, size
