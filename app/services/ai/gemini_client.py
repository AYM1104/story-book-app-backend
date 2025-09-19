# Gemini クライアント
import os
import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Gemini 2.5 Flash クライアント"""
    
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.7,
            max_output_tokens=2048,
            convert_system_message_to_human=True
        )
    
    async def generate_text(self, prompt: str, system_message: str = "") -> str:
        """テキスト生成"""
        try:
            messages = []
            if system_message:
                messages.append(("system", system_message))
            messages.append(("human", prompt))
            
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Gemini生成エラー: {str(e)}")
            raise
    
    async def generate_creative_text(self, prompt: str, system_message: str = "") -> str:
        """創造的なテキスト生成（温度設定を上げて多様性を増す）"""
        try:
            # 創造性を高めるために温度を上げたLLMを作成
            creative_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.google_api_key,
                temperature=0.9,  # より高い温度設定
                max_output_tokens=2048,
                convert_system_message_to_human=True
            )
            
            messages = []
            if system_message:
                messages.append(("system", system_message))
            messages.append(("human", prompt))
            
            response = await creative_llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Gemini創造的生成エラー: {str(e)}")
            raise
    
    async def analyze_story_elements(self, vision_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """物語要素を分析"""
        system_message = """あなたは物語分析の専門家です。画像の内容を基に、物語に必要な要素を分析し、不足している要素を特定してください。

物語に必要な要素:
1. キャラクター（character）: 主人公や登場人物
2. 設定（setting）: 場所や環境
3. 感情（emotion）: 気持ちや感情
4. 行動（action）: 出来事や行動
5. 問題（conflict）: 課題や問題
6. 解決（resolution）: 解決や結末

JSON形式で回答してください：
{
  "elements": {
    "character": {"value": "分析結果", "confidence": 80},
    "setting": {"value": "分析結果", "confidence": 70}
  },
  "missing_elements": ["conflict", "resolution"]
}"""
        
        prompt = f"画像の解析結果: {vision_analysis}"
        response = await self.generate_text(prompt, system_message)
        return self._parse_json_response(response)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """JSONレスポンスをパース"""
        import json
        import re
        
        try:
            # ```json で囲まれている場合を処理
            if '```json' in response_text:
                # ```json と ``` の間の内容を抽出
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
            
            # 通常のJSONブロックを検索
            # より柔軟な正規表現でネストしたJSONを検出
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_blocks = re.findall(json_pattern, response_text, re.DOTALL)
            
            if json_blocks:
                # 最も長いJSONブロックを選択
                longest_block = max(json_blocks, key=len)
                return json.loads(longest_block)
            
            # 従来の方法も試す
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning(f"JSON形式が見つかりません: {response_text[:200]}...")
                return {"elements": {}, "missing_elements": []}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {str(e)}")
            logger.error(f"レスポンス内容: {response_text[:500]}...")
            return {"elements": {}, "missing_elements": []}

# シングルトンインスタンス（遅延初期化）
_gemini_client = None

def get_gemini_client():
    """Geminiクライアントのシングルトンインスタンスを取得"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client