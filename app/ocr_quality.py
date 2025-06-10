import requests
import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
    def is_available(self) -> bool:
        """Ollama 서비스가 사용 가능한지 확인합니다."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 서비스 확인 실패: {e}")
            return False
    
    def query_llava(self, image_base64: str, prompt: str) -> Optional[str]:
        """LLaVA 모델을 사용하여 이미지에 대한 질의를 수행합니다."""
        if not self.is_available():
            logger.error("Ollama 서비스를 사용할 수 없습니다.")
            return None
            
        try:
            payload = {
                "model": "llava",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"LLaVA 호출 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"LLaVA 질의 중 오류 발생: {e}")
            return None

def assess_ocr_quality(image_base64: str, extracted_text: str = "") -> Dict:
    """이미지의 OCR 품질을 평가합니다."""
    
    quality_prompt = """
    이 이미지는 과학 논문의 첫 페이지입니다. 다음 기준으로 OCR 품질을 평가해주세요:

    1. 텍스트 선명도: 글자가 명확하게 보이는가?
    2. 레이아웃 복잡도: 다단, 표, 그림이 많아 OCR이 어려운가?
    3. 이미지 품질: 스캔 품질이나 해상도가 적절한가?
    4. 언어 혼재: 영어, 한국어, 수식 등이 복합적으로 나타나는가?

    다음 JSON 형식으로 답변해주세요:
    {
        "text_clarity": "excellent|good|fair|poor",
        "layout_complexity": "simple|moderate|complex|very_complex", 
        "image_quality": "excellent|good|fair|poor",
        "language_mix": "english_only|korean_only|mixed|math_heavy",
        "overall_quality": "excellent|good|fair|poor",
        "confidence_score": 0.85,
        "recommendations": "OCR 수행 권장 여부 및 이유"
    }
    """
    
    client = OllamaClient()
    
    # Ollama가 사용 불가능한 경우 기본값 반환
    if not client.is_available():
        logger.warning("Ollama를 사용할 수 없어 기본 OCR 품질 평가를 반환합니다.")
        return {
            "text_clarity": "unknown",
            "layout_complexity": "unknown", 
            "image_quality": "unknown",
            "language_mix": "unknown",
            "overall_quality": "unknown",
            "confidence_score": 0.0,
            "recommendations": "Ollama 서비스 불가로 자동 평가 불가",
            "service_available": False
        }
    
    try:
        # LLaVA를 사용하여 품질 평가
        response = client.query_llava(image_base64, quality_prompt)
        
        if response:
            # JSON 응답 파싱 시도
            try:
                # 응답에서 JSON 부분만 추출
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    quality_data = json.loads(json_str)
                    quality_data["service_available"] = True
                    return quality_data
            except json.JSONDecodeError:
                logger.warning("LLaVA 응답을 JSON으로 파싱할 수 없습니다.")
        
        # 파싱 실패 시 기본값 반환
        return {
            "text_clarity": "fair",
            "layout_complexity": "moderate",
            "image_quality": "fair", 
            "language_mix": "mixed",
            "overall_quality": "fair",
            "confidence_score": 0.5,
            "recommendations": "자동 평가 실패로 기본 OCR 수행 권장",
            "service_available": True,
            "raw_response": response
        }
        
    except Exception as e:
        logger.error(f"OCR 품질 평가 중 오류: {e}")
        return {
            "text_clarity": "unknown",
            "layout_complexity": "unknown",
            "image_quality": "unknown", 
            "language_mix": "unknown",
            "overall_quality": "unknown",
            "confidence_score": 0.0,
            "recommendations": f"평가 중 오류 발생: {str(e)}",
            "service_available": False
        }

def should_perform_ocr(quality_assessment: Dict, text_length: int = 0) -> bool:
    """OCR 품질 평가 결과를 바탕으로 OCR 수행 여부를 결정합니다."""
    
    # 텍스트가 매우 적으면 무조건 OCR 수행
    if text_length < 50:
        return True
    
    # 서비스를 사용할 수 없으면 안전하게 OCR 수행
    if not quality_assessment.get("service_available", False):
        return True
    
    overall_quality = quality_assessment.get("overall_quality", "unknown")
    confidence = quality_assessment.get("confidence_score", 0.0)
    
    # 품질이 나쁘거나 확신도가 낮으면 OCR 수행
    if overall_quality in ["poor", "unknown"] or confidence < 0.6:
        return True
    
    # 텍스트가 적당히 있고 품질이 좋으면 OCR 생략 가능
    if text_length > 200 and overall_quality in ["excellent", "good"]:
        return False
    
    # 기본적으로는 OCR 수행
    return True