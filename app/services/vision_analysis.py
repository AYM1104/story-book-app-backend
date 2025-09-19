import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from google.cloud import vision
from google.cloud.vision_v1 import types
from sqlalchemy.orm import Session
from app.models.upload_image import UploadImage
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Google Cloud Vision API を使用した画像解析サービス"""
    
    def __init__(self):
        # 認証ファイルのパスを明示的に設定
        credentials_path = os.path.join(os.path.dirname(__file__), "..", "secrets", "ayu1104-9462987945cd.json")
        credentials_path = os.path.abspath(credentials_path)
        
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            logger.info(f"Google Cloud認証ファイルを設定: {credentials_path}")
        else:
            logger.warning(f"認証ファイルが見つかりません: {credentials_path}")
        
        self.client = vision.ImageAnnotatorClient()
    
    def analyze_image(self, asset_id: int) -> Dict:
        """
        画像を解析してメタデータを返す
        
        Args:
            asset_id: アップロードされた画像のID
            
        Returns:
            Dict: 解析結果（tags, palette, geometry）
        """
        try:
            # データベースから画像情報を取得
            db = SessionLocal()
            try:
                upload_image = db.query(UploadImage).filter(UploadImage.id == asset_id).first()
                if not upload_image:
                    raise ValueError(f"Asset ID {asset_id} が見つかりません")
                
                # Vision API で画像を解析
                # ローカルファイルの場合は直接読み込み
                if upload_image.url.startswith('http://127.0.0.1:8000/uploads/'):
                    # ローカルファイルパスを取得
                    filename = upload_image.filename
                    file_path = os.path.join(os.path.dirname(__file__), "..", "uploads", filename)
                    file_path = os.path.abspath(file_path)
                    
                    if os.path.exists(file_path):
                        # ファイルを直接読み込み
                        with open(file_path, 'rb') as image_file:
                            image_content = image_file.read()
                        
                        image = types.Image()
                        image.content = image_content
                    else:
                        raise ValueError(f"画像ファイルが見つかりません: {file_path}")
                else:
                    # 公開URLの場合はそのまま使用
                    image_uri = upload_image.url
                    image = types.Image()
                    image.source.image_uri = image_uri
                
                # 複数の解析を並行実行
                responses = self.client.batch_annotate_images({
                    'requests': [
                        {
                            'image': image,
                            'features': [
                                {'type': types.Feature.Type.OBJECT_LOCALIZATION},
                                {'type': types.Feature.Type.LABEL_DETECTION},
                                {'type': types.Feature.Type.IMAGE_PROPERTIES},
                            ]
                        }
                    ]
                })
                
                response = responses.responses[0]
                
                # 解析結果を処理
                tags = self._extract_tags(response)
                palette = self._extract_palette(response)
                geometry = self._extract_geometry(response)
                
                return {
                    "tags": tags,
                    "palette": palette,
                    "geometry": geometry
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"画像解析エラー (asset_id: {asset_id}): {str(e)}")
            raise
    
    def _extract_tags(self, response: types.AnnotateImageResponse) -> List[str]:
        """タグを抽出（オブジェクト検出を優先、なければラベル検出）"""
        tags = []
        
        # オブジェクト検出を優先
        if response.localized_object_annotations:
            for obj in response.localized_object_annotations:
                tags.append(obj.name.lower())
        
        # オブジェクトが見つからない場合はラベル検出を使用
        if not tags and response.label_annotations:
            for label in response.label_annotations[:10]:  # 上位10個
                tags.append(label.description.lower())
        
        return list(set(tags))  # 重複を除去
    
    def _extract_palette(self, response: types.AnnotateImageResponse) -> List[Dict]:
        """ドミナントカラーを抽出（上位5色）"""
        palette = []
        
        if response.image_properties_annotation and response.image_properties_annotation.dominant_colors:
            colors = response.image_properties_annotation.dominant_colors.colors
            
            for color in colors[:5]:  # 上位5色
                palette.append({
                    "rgb": {
                        "r": int(color.color.red),
                        "g": int(color.color.green),
                        "b": int(color.color.blue)
                    },
                    "score": color.score
                })
        
        return palette
    
    def _extract_geometry(self, response: types.AnnotateImageResponse) -> Dict:
        """画像の幾何学情報を抽出"""
        geometry = {
            "width": 0,
            "height": 0,
            "subject_center": [0.5, 0.5]  # デフォルト値
        }
        
        # 画像サイズを取得
        if response.image_properties_annotation:
            # Vision API のレスポンスから画像サイズを取得する方法を確認
            # 通常は別途画像ファイルを読み込む必要がある
            pass
        
        # 最大オブジェクトの中心を計算
        if response.localized_object_annotations:
            largest_object = max(
                response.localized_object_annotations,
                key=lambda obj: self._calculate_area(obj.bounding_poly)
            )
            
            center = self._calculate_center(largest_object.bounding_poly)
            geometry["subject_center"] = center
        
        return geometry
    
    def _calculate_area(self, bounding_poly: types.BoundingPoly) -> float:
        """バウンディングポリゴンの面積を計算"""
        if not bounding_poly.normalized_vertices:
            return 0
        
        vertices = bounding_poly.normalized_vertices
        if len(vertices) < 3:
            return 0
        
        # 矩形の面積を計算（簡易版）
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]
        
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        
        return width * height
    
    def _calculate_center(self, bounding_poly: types.BoundingPoly) -> List[float]:
        """バウンディングポリゴンの中心を計算"""
        if not bounding_poly.normalized_vertices:
            return [0.5, 0.5]
        
        vertices = bounding_poly.normalized_vertices
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]
        
        center_x = (max(x_coords) + min(x_coords)) / 2
        center_y = (max(y_coords) + min(y_coords)) / 2
        
        return [center_x, center_y]
    
    def save_analysis_result(self, asset_id: int, analysis_result: Dict) -> bool:
        """
        解析結果をデータベースに保存
        
        Args:
            asset_id: アップロードされた画像のID
            analysis_result: 解析結果
            
        Returns:
            bool: 保存成功かどうか
        """
        try:
            db = SessionLocal()
            try:
                upload_image = db.query(UploadImage).filter(UploadImage.id == asset_id).first()
                if not upload_image:
                    raise ValueError(f"Asset ID {asset_id} が見つかりません")
                
                # meta_json に解析結果を保存
                upload_image.meta_json = json.dumps(analysis_result, ensure_ascii=False)
                db.commit()
                
                logger.info(f"解析結果を保存しました (asset_id: {asset_id})")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"解析結果保存エラー (asset_id: {asset_id}): {str(e)}")
            return False
    
    def get_analysis_result(self, asset_id: int) -> Optional[Dict]:
        """
        保存済みの解析結果を取得
        
        Args:
            asset_id: アップロードされた画像のID
            
        Returns:
            Optional[Dict]: 解析結果（保存されていない場合はNone）
        """
        try:
            db = SessionLocal()
            try:
                upload_image = db.query(UploadImage).filter(UploadImage.id == asset_id).first()
                if not upload_image:
                    raise ValueError(f"Asset ID {asset_id} が見つかりません")
                
                if upload_image.meta_json:
                    return json.loads(upload_image.meta_json)
                else:
                    return None
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"解析結果取得エラー (asset_id: {asset_id}): {str(e)}")
            return None


# シングルトンインスタンス
vision_service = VisionAnalysisService()
