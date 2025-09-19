from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.services.vision_analysis import vision_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["asset-analysis"])


@router.post("/{id}/analyze", response_model=Dict[str, Any])
async def analyze_asset(id: int):
    """
    指定されたアセットを Google Cloud Vision API で解析し、結果をデータベースに保存する
    
    Args:
        id: 解析対象のアセットID
        
    Returns:
        Dict: 解析結果（tags, palette, geometry）
    """
    try:
        logger.info(f"アセット解析開始 (id: {id})")
        
        # Vision API で画像を解析
        analysis_result = vision_service.analyze_image(id)
        
        # 解析結果をデータベースに保存
        save_success = vision_service.save_analysis_result(id, analysis_result)
        
        if not save_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="解析結果の保存に失敗しました"
            )
        
        logger.info(f"アセット解析完了 (id: {id})")
        
        return {
            "id": id,
            "status": "success",
            "analysis": analysis_result
        }
        
    except ValueError as e:
        logger.warning(f"アセット解析エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"アセット解析エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="画像解析中にエラーが発生しました"
        )


@router.get("/{id}/features", response_model=Dict[str, Any])
async def get_asset_features(id: int):
    """
    指定されたアセットの保存済み解析結果を取得する
    
    Args:
        id: 対象のアセットID
        
    Returns:
        Dict: 保存済みの解析結果
    """
    try:
        logger.info(f"アセット特徴取得開始 (id: {id})")
        
        # 保存済みの解析結果を取得
        analysis_result = vision_service.get_analysis_result(id)
        
        if analysis_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"アセット {id} の解析結果が見つかりません。先に /analyze エンドポイントで解析を実行してください。"
            )
        
        logger.info(f"アセット特徴取得完了 (id: {id})")
        
        return {
            "id": id,
            "status": "success",
            "analysis": analysis_result
        }
        
    except ValueError as e:
        logger.warning(f"アセット特徴取得エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        # HTTPException はそのまま再発生
        raise
    except Exception as e:
        logger.error(f"アセット特徴取得エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解析結果の取得中にエラーが発生しました"
        )
