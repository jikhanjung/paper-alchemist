import numpy as np
import hashlib
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Tuple, Optional
import re

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """BGE-M3 모델을 초기화합니다."""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"임베딩 모델 {model_name} 로드 완료")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            raise

    def preprocess_text(self, text: str) -> str:
        """텍스트를 전처리합니다."""
        if not text:
            return ""
        
        # 과도한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 불필요한 문자 제거 (하지만 과학 논문의 특수문자는 보존)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\'\/\\\@\#\$\%\^\&\*\+\=\|\~\`]', ' ', text)
        
        # 연속된 공백 다시 정리
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """긴 텍스트를 청크로 나눕니다."""
        if not text:
            return []
        
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            
            if end >= len(words):
                break
                
            start = end - overlap
        
        return chunks

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """단일 텍스트에 대한 임베딩을 생성합니다."""
        if not text or not text.strip():
            return None
        
        try:
            processed_text = self.preprocess_text(text)
            if not processed_text:
                return None
            
            embedding = self.model.encode(processed_text, normalize_embeddings=True)
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None

    def generate_document_embedding(self, text: str) -> Tuple[Optional[List[float]], List[dict]]:
        """문서 전체에 대한 임베딩을 생성합니다. 청크별 임베딩의 평균을 계산합니다."""
        if not text or not text.strip():
            return None, []
        
        try:
            # 텍스트를 청크로 분할
            chunks = self.chunk_text(text)
            if not chunks:
                return None, []
            
            chunk_embeddings = []
            chunk_info = []
            
            for i, chunk in enumerate(chunks):
                embedding = self.generate_embedding(chunk)
                if embedding is not None:
                    chunk_embeddings.append(embedding)
                    chunk_info.append({
                        "chunk_id": i,
                        "text": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                        "embedding_dim": len(embedding)
                    })
            
            if not chunk_embeddings:
                return None, []
            
            # 청크 임베딩들의 평균 계산
            avg_embedding = np.mean(chunk_embeddings, axis=0).tolist()
            
            return avg_embedding, chunk_info
            
        except Exception as e:
            logger.error(f"문서 임베딩 생성 실패: {e}")
            return None, []

    def compute_content_id(self, embedding: List[float]) -> str:
        """임베딩 벡터로부터 내용 기반 고유 ID를 생성합니다."""
        try:
            # 임베딩을 float32 바이트로 변환
            byte_vec = np.array(embedding, dtype=np.float32).tobytes()
            # SHA-256 해시 계산
            content_id = hashlib.sha256(byte_vec).hexdigest()
            return content_id
        except Exception as e:
            logger.error(f"Content ID 생성 실패: {e}")
            return None

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """두 임베딩 간의 코사인 유사도를 계산합니다."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 코사인 유사도 계산
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0

def process_text_embedding(text: str) -> dict:
    """텍스트에 대한 전체 임베딩 처리를 수행합니다."""
    generator = EmbeddingGenerator()
    
    # 문서 임베딩 생성
    embedding, chunk_info = generator.generate_document_embedding(text)
    
    result = {
        "embedding": embedding,
        "embedding_dim": len(embedding) if embedding else 0,
        "chunk_count": len(chunk_info),
        "chunk_info": chunk_info,
        "content_id": None
    }
    
    # Content ID 생성
    if embedding:
        content_id = generator.compute_content_id(embedding)
        result["content_id"] = content_id
    
    return result