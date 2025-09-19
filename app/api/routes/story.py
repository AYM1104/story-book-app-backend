from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.session import SessionLocal
from app.agents.story_agent import get_story_agent
from app.models.story_answer import StoryAnswer
from app.schemas.story_answer import AnswerSubmissionRequest, StoryAnswerCreate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/story", tags=["story"])

class QuestionsRequest(BaseModel):
    missing_elements: List[str]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{id}/analyze", response_model=Dict[str, Any])
async def analyze_image_for_story(id: int):
    """
    画像を物語生成用に分析
    
    Args:
        id: 画像のID
        
    Returns:
        Dict: 分析結果と不足要素
    """
    try:
        logger.info(f"物語分析開始 (id: {id})")
        
        story_agent = get_story_agent()
        result = await story_agent.analyze_image_for_story(id)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "分析中にエラーが発生しました")
            )
        
        logger.info(f"物語分析完了 (id: {id})")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"物語分析エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="物語分析中にエラーが発生しました"
        )

@router.post("/{id}/questions", response_model=Dict[str, Any])
async def generate_story_questions(
    id: int,
    request: QuestionsRequest,
    db: Session = Depends(get_db)
):
    """
    不足要素を基に質問を生成してDBに保存
    
    Args:
        id: 画像のID
        request: 不足要素のリストを含むリクエストボディ
        db: データベースセッション
        
    Returns:
        Dict: 生成された質問とDB保存結果
    """
    try:
        logger.info(f"質問生成開始 (id: {id})")
        
        story_agent = get_story_agent()
        questions = await story_agent.generate_questions(id, request.missing_elements)
        
        # 質問をDBに保存
        saved_questions = await story_agent.save_questions_to_db(db, id, questions)
        
        return {
            "id": id,
            "missing_elements": request.missing_elements,
            "questions": questions,
            "saved_questions": saved_questions,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"質問生成エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="質問生成中にエラーが発生しました"
        )

@router.post("/answers", response_model=Dict[str, Any])
async def submit_story_answers(
    request: AnswerSubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    物語の質問への回答をDBに保存
    
    Args:
        request: 回答データのリストを含むリクエストボディ
        db: データベースセッション
        
    Returns:
        Dict: 保存結果
    """
    try:
        logger.info(f"回答保存開始 (回答数: {len(request.answers)})")
        
        saved_answers = []
        
        for answer_data in request.answers:
            # StoryAnswerモデルのインスタンスを作成
            db_answer = StoryAnswer(
                question_id=answer_data.question_id,
                user_id=answer_data.user_id,
                answer_text=answer_data.answer_text,
                selected_option=answer_data.selected_option,
                followup_answers=answer_data.followup_answers
            )
            
            # DBに追加
            db.add(db_answer)
            db.flush()  # IDを取得するためにflush
            
            saved_answers.append({
                "id": db_answer.id,
                "question_id": db_answer.question_id,
                "user_id": db_answer.user_id,
                "answer_text": db_answer.answer_text,
                "selected_option": db_answer.selected_option,
                "followup_answers": db_answer.followup_answers,
                "created_at": db_answer.created_at
            })
        
        # トランザクションをコミット
        db.commit()
        
        logger.info(f"回答保存完了 (保存数: {len(saved_answers)})")
        
        return {
            "status": "success",
            "message": f"{len(saved_answers)}件の回答を保存しました",
            "saved_answers": saved_answers
        }
        
    except Exception as e:
        logger.error(f"回答保存エラー: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="回答保存中にエラーが発生しました"
        )

@router.post("/{id}/validate", response_model=Dict[str, Any])
async def validate_collected_information(
    id: int,
    db: Session = Depends(get_db)
):
    """
    収集した情報の品質を検証
    
    Args:
        id: 画像のID
        db: データベースセッション
        
    Returns:
        Dict: 検証結果
    """
    try:
        logger.info(f"情報検証開始 (id: {id})")
        
        # DBから質問と回答を取得
        from app.models.story_question import StoryQuestion
        from app.models.story_answer import StoryAnswer
        
        questions = db.query(StoryQuestion).filter(StoryQuestion.image_id == id).all()
        answers = db.query(StoryAnswer).join(StoryQuestion).filter(StoryQuestion.image_id == id).all()
        
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された画像の質問が見つかりません"
            )
        
        # 質問と回答を辞書形式に変換
        questions_data = []
        for q in questions:
            questions_data.append({
                "id": q.id,
                "target_element": q.target_element,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "followups": q.followups,
                "reason": q.reason
            })
        
        answers_data = []
        for a in answers:
            answers_data.append({
                "id": a.id,
                "question_id": a.question_id,
                "answer_text": a.answer_text,
                "selected_option": a.selected_option,
                "followup_answers": a.followup_answers
            })
        
        # 情報検証を実行
        story_agent = get_story_agent()
        validation_result = await story_agent.validate_collected_information(
            id, questions_data, answers_data
        )
        
        if validation_result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=validation_result.get("message", "情報検証中にエラーが発生しました")
            )
        
        logger.info(f"情報検証完了 (id: {id})")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"情報検証エラー (id: {id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="情報検証中にエラーが発生しました"
        )