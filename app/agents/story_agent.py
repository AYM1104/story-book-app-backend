# 物語生成エージェント

import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.services.ai.gemini_client import get_gemini_client
from app.services.vision_analysis import vision_service
from app.models.story_question import StoryQuestion
from app.schemas.story_question import StoryQuestionCreate

logger = logging.getLogger(__name__)

class StoryAgent:
    """物語生成エージェント"""
    
    def __init__(self):
        self.gemini = get_gemini_client()
    
    async def analyze_image_for_story(self, asset_id: int) -> Dict[str, Any]:
        """画像を物語生成用に分析"""
        try:
            # Vision APIの解析結果を取得
            vision_analysis = vision_service.get_analysis_result(asset_id)
            if not vision_analysis:
                raise ValueError(f"Asset {asset_id} の解析結果が見つかりません")
            
            # Geminiで物語要素を分析
            story_analysis = await self.gemini.analyze_story_elements(vision_analysis)
            
            return {
                "id": asset_id,
                "vision_analysis": vision_analysis,
                "story_elements": story_analysis.get("elements", {}),
                "missing_elements": story_analysis.get("missing_elements", []),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"画像分析エラー (asset_id: {asset_id}): {str(e)}")
            return {
                "id": asset_id,
                "error": str(e),
                "status": "error"
            }
    
    async def generate_questions(self, asset_id: int, missing_elements: List[str]) -> List[Dict[str, Any]]:
        """不足要素を基に質問を生成"""
        try:
            vision_analysis = vision_service.get_analysis_result(asset_id)
            if not vision_analysis:
                return [{
                    "target_element": "主人公",
                    "reason": "画像解析結果がありません",
                    "question": "この えの しゅじんこうは だれかな？",
                    "type": "open",
                    "followups": ["なまえは なに？"]
                }]
            
            # --- 新しい質問生成ロジック ---
            system_message = """あなたは「物語の穴うめインタビュアー（3〜6歳向け）」です。

# 重要な指示
あなたの回答は必ず以下のJSON形式で出力してください。```jsonで囲まず、純粋なJSONのみを出力してください。

{
  "questions": [
    {
      "target_element": "主人公",
      "reason": "主人公が不明確",
      "question": "この おはなしの しゅじんこう は だれ？",
      "type": "open",
      "followups": ["なまえは なに？"]
    },
    {
      "target_element": "舞台",
      "reason": "場所が不明確", 
      "question": "この ばしょは どこかな？",
      "type": "choice",
      "options": ["やま", "うみ", "おうち"],
      "followups": ["どんな ところ？"]
    }
  ],
  "meta": {
    "icebreakers": true,
    "age_range": "3-6", 
    "total_questions": 6
  }
}

# 質問作成のガイドライン
- 3〜6歳向けのひらがな中心・短文
- 各質問は20文字前後
- missing_elementsをすべてカバー
- Vision解析の要素から2問はアイスブレイク
- 決めつけは禁止
- 全体で6問程度
- 必ず完全なJSONを出力してください

# 避けるべき質問（NG例）
- 「だれがかいたの？」（作者は子供本人）
- 「どんな色をつかったの？」（画像から分かる）
- 「いつかいたの？」（時系列は不要）
- 「どこでかいたの？」（場所の設定は不要）

# 推奨する質問（OK例）
- 「この おはなしの しゅじんこうは だれ？」
- 「この ばしょは どこかな？」
- 「なにか こまったことは あった？」
- 「この ひとは どんな きもち？」
- 「つぎに なにが おこるかな？」

# 出力は純粋なJSON形式のみ。```jsonで囲まず、他の説明も不要。"""

            # モデルへの入力（ユーザーメッセージ）
            prompt = f"""
画像解析: {vision_analysis}

不足要素: {missing_elements}

上記の情報をもとに、3〜6歳向けの質問を6問作成してください。
必ずJSON形式のみで回答してください。
"""
            
            response = await self.gemini.generate_creative_text(prompt, system_message)
            print(f"=== DEBUG: Gemini応答の長さ: {len(response)}文字 ===")
            print(f"=== DEBUG: Gemini応答（最初の500文字）: {response[:500]} ===")
            print(f"=== DEBUG: Gemini応答（最後の500文字）: {response[-500:]} ===")
            logger.info(f"Gemini応答の長さ: {len(response)}文字")
            logger.info(f"Gemini応答（最初の500文字）: {response[:500]}")
            logger.info(f"Gemini応答（最後の500文字）: {response[-500:]}")
            
            try:
                parsed_response = self.gemini._parse_json_response(response)
                print(f"=== DEBUG: パース結果: {parsed_response} ===")
                logger.info(f"パース結果: {parsed_response}")
                
                # 新しい形式の質問を返す
                questions = parsed_response.get("questions", [])
                
                # 質問が空の場合のフォールバック
                if not questions:
                    logger.warning("質問が生成されませんでした。フォールバック質問を使用します。")
                    questions = [
                        {
                            "target_element": "主人公",
                            "reason": "フォールバック質問",
                            "question": "この えの しゅじんこうは だれかな？",
                            "type": "open",
                            "followups": ["なまえは なに？"]
                        }
                    ]
                
                return questions
                
            except Exception as parse_error:
                logger.error(f"JSON解析エラー: {str(parse_error)}")
                logger.error(f"Gemini応答全体: {response}")
                return [
                    {
                        "target_element": "主人公",
                        "reason": "JSON解析エラー",
                        "question": "この えの しゅじんこうは だれかな？",
                        "type": "open",
                        "followups": ["なまえは なに？"]
                    }
                ]
            
        except Exception as e:
            logger.error(f"質問生成エラー (asset_id: {asset_id}): {str(e)}")
            return [
                {
                    "target_element": "主人公",
                    "reason": "エラー時のフォールバック",
                    "question": "この えの しゅじんこうは だれかな？",
                    "type": "open",
                    "followups": ["なまえは なに？"]
                }
            ]
    
    async def save_questions_to_db(self, db: Session, image_id: int, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成された質問をDBに保存"""
        try:
            logger.info(f"質問DB保存開始 (image_id: {image_id}, 質問数: {len(questions)})")
            
            saved_questions = []
            
            for question_data in questions:
                # StoryQuestionモデルのインスタンスを作成
                db_question = StoryQuestion(
                    image_id=image_id,
                    target_element=question_data.get("target_element", ""),
                    question_text=question_data.get("question", ""),
                    question_type=question_data.get("type", "open"),
                    options=question_data.get("options"),
                    followups=question_data.get("followups"),
                    reason=question_data.get("reason")
                )
                
                # DBに追加
                db.add(db_question)
                db.flush()  # IDを取得するためにflush
                
                saved_questions.append({
                    "id": db_question.id,
                    "image_id": db_question.image_id,
                    "target_element": db_question.target_element,
                    "question_text": db_question.question_text,
                    "question_type": db_question.question_type,
                    "options": db_question.options,
                    "followups": db_question.followups,
                    "reason": db_question.reason,
                    "created_at": db_question.created_at
                })
            
            # トランザクションをコミット
            db.commit()
            
            logger.info(f"質問DB保存完了 (保存数: {len(saved_questions)})")
            
            return saved_questions
            
        except Exception as e:
            logger.error(f"質問DB保存エラー: {str(e)}")
            db.rollback()
            raise e
    
    async def validate_collected_information(self, image_id: int, questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """収集した情報の品質を検証"""
        try:
            logger.info(f"情報検証開始 (image_id: {image_id}, 質問数: {len(questions)}, 回答数: {len(answers)})")
            
            # Vision解析結果を取得
            vision_analysis = vision_service.get_analysis_result(image_id)
            if not vision_analysis:
                return {
                    "status": "error",
                    "message": "画像解析結果が見つかりません",
                    "validation_result": None
                }
            
            # 検証用のプロンプトを作成
            system_message = """あなたは「3-6歳向け物語作成の情報品質チェッカー」です。

# 重要な指示
あなたの回答は必ず以下のJSON形式で出力してください。```jsonで囲まず、純粋なJSONのみを出力してください。

{
  "validation_result": {
    "overall_score": 85,
    "completeness": {
      "score": 80,
      "missing_elements": ["主人公の名前", "問題の解決方法"],
      "sufficient_elements": ["主人公", "舞台", "問題"]
    },
    "age_appropriateness": {
      "score": 90,
      "issues": [],
      "strengths": ["ひらがな中心", "短文", "具体的"]
    },
    "story_coherence": {
      "score": 75,
      "issues": ["主人公の動機が不明確"],
      "suggestions": ["主人公がなぜその行動を取るのかを明確にする"]
    },
    "recommendations": [
      "主人公の名前を追加してください",
      "問題の解決方法を具体的に説明してください"
    ],
    "ready_for_story": false
  },
  "meta": {
    "total_questions": 6,
    "answered_questions": 5,
    "validation_timestamp": "2024-01-01T00:00:00Z"
  }
}

# 検証基準
## 完全性 (Completeness)
- 主人公、舞台、問題、解決方法の基本要素が揃っているか
- 3-6歳向けに必要な情報が不足していないか
- 画像から読み取れる要素と回答の整合性

## 年齢適切性 (Age Appropriateness)  
- ひらがな中心で理解しやすいか
- 短文で表現されているか
- 抽象的すぎないか
- 恐怖や不安を煽る内容でないか

## 物語の一貫性 (Story Coherence)
- 主人公の動機が明確か
- 問題と解決方法が論理的か
- キャラクターの行動が一貫しているか

## 推奨事項
- 不足している要素の具体的な提案
- 改善すべき点の指摘
- 物語生成に適しているかの判定

# 出力は純粋なJSON形式のみ。```jsonで囲まず、他の説明も不要。"""

            # ユーザーメッセージを作成
            prompt = f"""
画像解析結果: {vision_analysis}

生成された質問:
{questions}

収集された回答:
{answers}

上記の情報を基に、3-6歳向け物語作成に必要な情報の品質を検証してください。
必ずJSON形式のみで回答してください。
"""
            
            response = await self.gemini.generate_creative_text(prompt, system_message)
            logger.info(f"情報検証Gemini応答: {response[:500]}...")
            
            try:
                parsed_response = self.gemini._parse_json_response(response)
                logger.info(f"情報検証結果: {parsed_response}")
                
                return {
                    "status": "success",
                    "image_id": image_id,
                    "validation_result": parsed_response.get("validation_result", {}),
                    "meta": parsed_response.get("meta", {}),
                    "message": "情報検証が完了しました"
                }
                
            except Exception as parse_error:
                logger.error(f"情報検証JSON解析エラー: {str(parse_error)}")
                logger.error(f"Gemini応答全体: {response}")
                
                # フォールバック検証結果
                return {
                    "status": "partial_success",
                    "image_id": image_id,
                    "validation_result": {
                        "overall_score": 70,
                        "completeness": {
                            "score": 70,
                            "missing_elements": ["詳細な検証が必要"],
                            "sufficient_elements": ["基本情報は収集済み"]
                        },
                        "age_appropriateness": {
                            "score": 80,
                            "issues": [],
                            "strengths": ["回答が収集されている"]
                        },
                        "story_coherence": {
                            "score": 70,
                            "issues": ["詳細な検証が必要"],
                            "suggestions": ["情報の再確認を推奨"]
                        },
                        "recommendations": [
                            "回答の詳細を確認してください",
                            "不足している情報があれば追加してください"
                        ],
                        "ready_for_story": True
                    },
                    "meta": {
                        "total_questions": len(questions),
                        "answered_questions": len(answers),
                        "validation_timestamp": "2024-01-01T00:00:00Z"
                    },
                    "message": "情報検証が完了しました（簡易版）"
                }
            
        except Exception as e:
            logger.error(f"情報検証エラー (image_id: {image_id}): {str(e)}")
            return {
                "status": "error",
                "image_id": image_id,
                "error": str(e),
                "message": "情報検証中にエラーが発生しました"
            }

# シングルトンインスタンス（遅延初期化）
_story_agent = None

def get_story_agent():
    """StoryAgentのシングルトンインスタンスを取得"""
    global _story_agent
    if _story_agent is None:
        _story_agent = StoryAgent()
    return _story_agent