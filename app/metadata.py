import requests
import json
import re
import logging
from typing import Dict, Optional, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataExtractor:
    def __init__(self, ollama_base_url: str = None):
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://172.19.96.1:11434")
        
    def is_ollama_available(self) -> bool:
        """Ollama 서비스 가용성을 확인합니다."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 서비스 확인 실패: {e}")
            return False
    
    def extract_with_llm(self, text: str, model: str = "llama3.1:latest") -> Optional[Dict]:
        """LLM을 사용하여 메타데이터를 추출합니다."""
        if not self.is_ollama_available():
            logger.error("Ollama 서비스를 사용할 수 없습니다.")
            return None
        
        prompt = f"""
다음은 과학 논문의 텍스트입니다. 이 논문에서 서지정보를 추출하여 JSON 형식으로 제공해주세요.

논문 텍스트:
{text[:3000]}

다음 JSON 형식으로 정확히 답변해주세요:
{{
    "title": "논문 제목",
    "authors": ["저자1", "저자2", "저자3"],
    "abstract": "논문 초록 (200자 이내 요약)",
    "keywords": ["키워드1", "키워드2", "키워드3"],
    "publication_year": 2024,
    "journal": "저널명",
    "doi": "DOI 번호 (있는 경우)",
    "institution": ["소속기관1", "소속기관2"],
    "language": "en|ko|mixed",
    "paper_type": "research|review|conference|thesis",
    "field": "연구분야"
}}

정보가 명확하지 않은 경우 null을 사용하고, 추측하지 마세요.
"""

        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                # JSON 파싱 시도
                try:
                    json_start = llm_response.find('{')
                    json_end = llm_response.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = llm_response[json_start:json_end]
                        metadata = json.loads(json_str)
                        return metadata
                except json.JSONDecodeError as e:
                    logger.warning(f"LLM 응답 JSON 파싱 실패: {e}")
                    return {"raw_response": llm_response}
            else:
                logger.error(f"LLM 호출 실패: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 메타데이터 추출 중 오류: {e}")
            return None

    def extract_basic_metadata(self, text: str) -> Dict:
        """규칙 기반으로 기본 메타데이터를 추출합니다."""
        metadata = {
            "title": None,
            "authors": [],
            "abstract": None,
            "keywords": [],
            "publication_year": None,
            "journal": None,
            "doi": None,
            "institution": [],
            "language": "unknown",
            "paper_type": "unknown",
            "field": None
        }
        
        if not text:
            return metadata
        
        # 언어 감지
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = korean_chars + english_chars
        
        if total_chars > 0:
            korean_ratio = korean_chars / total_chars
            if korean_ratio > 0.3:
                metadata["language"] = "ko" if korean_ratio > 0.7 else "mixed"
            else:
                metadata["language"] = "en"
        
        # DOI 추출
        doi_pattern = r'(?:doi:|DOI:)\s*(10\.\d+/[^\s]+)'
        doi_match = re.search(doi_pattern, text, re.IGNORECASE)
        if doi_match:
            metadata["doi"] = doi_match.group(1)
        
        # 연도 추출 (4자리 숫자)
        year_pattern = r'\b(19|20)\d{2}\b'
        year_matches = re.findall(year_pattern, text)
        if year_matches:
            years = [int(y) for y in year_matches if 1900 <= int(y) <= datetime.now().year]
            if years:
                metadata["publication_year"] = max(years)  # 가장 최근 연도 사용
        
        # 제목 추출 (첫 번째 줄이나 큰 텍스트 블록)
        lines = text.split('\n')
        for line in lines[:5]:  # 첫 5줄에서 제목 찾기
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                metadata["title"] = line
                break
        
        # 키워드 추출 (Keywords: 섹션 찾기)
        keyword_pattern = r'(?:keywords?|key\s*words?)[:：]\s*([^\n]+)'
        keyword_match = re.search(keyword_pattern, text, re.IGNORECASE)
        if keyword_match:
            keywords_text = keyword_match.group(1)
            keywords = [k.strip() for k in re.split(r'[,;]', keywords_text) if k.strip()]
            metadata["keywords"] = keywords[:10]  # 최대 10개
        
        # 초록 추출 (Abstract 섹션 찾기)
        abstract_pattern = r'(?:abstract|초록)[:：]\s*([^。\n]{50,500})'
        abstract_match = re.search(abstract_pattern, text, re.IGNORECASE | re.DOTALL)
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            metadata["abstract"] = abstract_text[:500]  # 최대 500자
        
        return metadata

def extract_paper_metadata(text: str) -> Dict:
    """논문 텍스트에서 메타데이터를 추출합니다."""
    extractor = MetadataExtractor()
    
    # 먼저 규칙 기반 추출
    basic_metadata = extractor.extract_basic_metadata(text)
    
    # LLM을 사용한 고급 추출 시도
    llm_metadata = extractor.extract_with_llm(text)
    
    # 결과 병합
    if llm_metadata:
        # LLM 결과로 업데이트 (None이 아닌 값만)
        for key, value in llm_metadata.items():
            if value is not None and key in basic_metadata:
                basic_metadata[key] = value
        
        basic_metadata["extraction_method"] = "llm_enhanced"
        basic_metadata["llm_available"] = True
    else:
        basic_metadata["extraction_method"] = "rule_based"
        basic_metadata["llm_available"] = False
    
    # 추출 시간 기록
    basic_metadata["extracted_at"] = datetime.now().isoformat()
    
    return basic_metadata

def validate_metadata(metadata: Dict) -> Dict:
    """메타데이터의 유효성을 검사하고 정리합니다."""
    validated = metadata.copy()
    
    # 제목 길이 제한
    if validated.get("title") and len(validated["title"]) > 300:
        validated["title"] = validated["title"][:300] + "..."
    
    # 저자 수 제한
    if validated.get("authors") and len(validated["authors"]) > 20:
        validated["authors"] = validated["authors"][:20]
    
    # 키워드 수 제한
    if validated.get("keywords") and len(validated["keywords"]) > 15:
        validated["keywords"] = validated["keywords"][:15]
    
    # 연도 유효성 검사
    if validated.get("publication_year"):
        year = validated["publication_year"]
        if not isinstance(year, int) or year < 1900 or year > datetime.now().year + 1:
            validated["publication_year"] = None
    
    return validated
