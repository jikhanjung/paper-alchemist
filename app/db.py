import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PaperDatabase:
    def __init__(self, db_path: str = "data/papers.db"):
        """SQLite 데이터베이스를 초기화합니다."""
        self.db_path = db_path
        
        # 데이터베이스 디렉토리 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 테이블 초기화
        self.init_tables()
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결을 관리합니다."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"데이터베이스 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_tables(self):
        """데이터베이스 테이블을 초기화합니다."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # papers 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    doc_id TEXT PRIMARY KEY,
                    content_id TEXT UNIQUE,
                    filename TEXT NOT NULL,
                    file_size INTEGER,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_status TEXT DEFAULT 'pending',
                    
                    -- OCR 관련
                    ocr_performed BOOLEAN DEFAULT FALSE,
                    original_text_length INTEGER,
                    ocr_text_length INTEGER,
                    
                    -- 메타데이터
                    title TEXT,
                    authors TEXT,  -- JSON 배열
                    abstract TEXT,
                    keywords TEXT,  -- JSON 배열
                    publication_year INTEGER,
                    journal TEXT,
                    doi TEXT,
                    institution TEXT,  -- JSON 배열
                    language TEXT,
                    paper_type TEXT,
                    field TEXT,
                    
                    -- 임베딩 정보
                    embedding_dim INTEGER,
                    chunk_count INTEGER,
                    
                    -- 처리 메타정보
                    extraction_method TEXT,
                    llm_available BOOLEAN,
                    processed_at TIMESTAMP,
                    
                    UNIQUE(content_id)
                )
            ''')
            
            # embeddings 테이블 (벡터 저장)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    doc_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES papers (doc_id)
                )
            ''')
            
            # ocr_quality 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ocr_quality (
                    doc_id TEXT PRIMARY KEY,
                    text_clarity TEXT,
                    layout_complexity TEXT,
                    image_quality TEXT,
                    language_mix TEXT,
                    overall_quality TEXT,
                    confidence_score REAL,
                    recommendations TEXT,
                    service_available BOOLEAN,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc_id) REFERENCES papers (doc_id)
                )
            ''')
            
            # processing_log 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    step TEXT,
                    status TEXT,
                    message TEXT,
                    duration_seconds REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc_id) REFERENCES papers (doc_id)
                )
            ''')
            
            conn.commit()
            logger.info("데이터베이스 테이블 초기화 완료")
    
    def save_paper(self, doc_id: str, filename: str, file_size: int, 
                   content_id: str = None) -> bool:
        """논문 기본 정보를 저장합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO papers 
                    (doc_id, content_id, filename, file_size, upload_time, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (doc_id, content_id, filename, file_size, 
                      datetime.now().isoformat(), 'processing'))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"논문 저장 실패: {e}")
            return False
    
    def update_ocr_info(self, doc_id: str, ocr_result: Dict) -> bool:
        """OCR 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE papers SET
                        ocr_performed = ?,
                        original_text_length = ?,
                        ocr_text_length = ?
                    WHERE doc_id = ?
                ''', (
                    ocr_result.get('ocr_performed', False),
                    len(ocr_result.get('original_text', '')),
                    len(ocr_result.get('ocr_text', '')),
                    doc_id
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"OCR 정보 업데이트 실패: {e}")
            return False
    
    def save_ocr_quality(self, doc_id: str, quality_data: Dict) -> bool:
        """OCR 품질 평가 결과를 저장합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ocr_quality 
                    (doc_id, text_clarity, layout_complexity, image_quality, 
                     language_mix, overall_quality, confidence_score, 
                     recommendations, service_available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doc_id,
                    quality_data.get('text_clarity'),
                    quality_data.get('layout_complexity'), 
                    quality_data.get('image_quality'),
                    quality_data.get('language_mix'),
                    quality_data.get('overall_quality'),
                    quality_data.get('confidence_score'),
                    quality_data.get('recommendations'),
                    quality_data.get('service_available', False)
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"OCR 품질 저장 실패: {e}")
            return False
    
    def save_metadata(self, doc_id: str, metadata: Dict) -> bool:
        """메타데이터를 저장합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE papers SET
                        title = ?, authors = ?, abstract = ?, keywords = ?,
                        publication_year = ?, journal = ?, doi = ?,
                        institution = ?, language = ?, paper_type = ?, field = ?,
                        extraction_method = ?, llm_available = ?
                    WHERE doc_id = ?
                ''', (
                    metadata.get('title'),
                    json.dumps(metadata.get('authors', []), ensure_ascii=False),
                    metadata.get('abstract'),
                    json.dumps(metadata.get('keywords', []), ensure_ascii=False),
                    metadata.get('publication_year'),
                    metadata.get('journal'),
                    metadata.get('doi'),
                    json.dumps(metadata.get('institution', []), ensure_ascii=False),
                    metadata.get('language'),
                    metadata.get('paper_type'),
                    metadata.get('field'),
                    metadata.get('extraction_method'),
                    metadata.get('llm_available', False),
                    doc_id
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
            return False
    
    def save_embedding(self, doc_id: str, embedding: List[float], 
                      embedding_info: Dict) -> bool:
        """임베딩을 저장합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 임베딩 벡터를 BLOB으로 저장
                import numpy as np
                embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO embeddings (doc_id, embedding)
                    VALUES (?, ?)
                ''', (doc_id, embedding_blob))
                
                # papers 테이블의 임베딩 정보 업데이트
                cursor.execute('''
                    UPDATE papers SET
                        embedding_dim = ?,
                        chunk_count = ?,
                        content_id = ?
                    WHERE doc_id = ?
                ''', (
                    embedding_info.get('embedding_dim', 0),
                    embedding_info.get('chunk_count', 0),
                    embedding_info.get('content_id'),
                    doc_id
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"임베딩 저장 실패: {e}")
            return False
    
    def complete_processing(self, doc_id: str) -> bool:
        """처리 완료 상태로 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE papers SET
                        processing_status = 'completed',
                        processed_at = ?
                    WHERE doc_id = ?
                ''', (datetime.now().isoformat(), doc_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"처리 완료 업데이트 실패: {e}")
            return False
    
    def get_paper_metadata(self, doc_id: str) -> Optional[Dict]:
        """논문 메타데이터를 조회합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT p.*, q.* FROM papers p
                    LEFT JOIN ocr_quality q ON p.doc_id = q.doc_id
                    WHERE p.doc_id = ?
                ''', (doc_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # JSON 필드 파싱
                    for field in ['authors', 'keywords', 'institution']:
                        if result.get(field):
                            try:
                                result[field] = json.loads(result[field])
                            except:
                                result[field] = []
                    return result
                return None
        except Exception as e:
            logger.error(f"메타데이터 조회 실패: {e}")
            return None
    
    def get_embedding(self, doc_id: str) -> Optional[List[float]]:
        """임베딩을 조회합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT embedding FROM embeddings WHERE doc_id = ?', (doc_id,))
                row = cursor.fetchone()
                
                if row:
                    import numpy as np
                    embedding_array = np.frombuffer(row['embedding'], dtype=np.float32)
                    return embedding_array.tolist()
                return None
        except Exception as e:
            logger.error(f"임베딩 조회 실패: {e}")
            return None
    
    def log_processing_step(self, doc_id: str, step: str, status: str, 
                          message: str = None, duration: float = None):
        """처리 단계를 로그에 기록합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO processing_log 
                    (doc_id, step, status, message, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                ''', (doc_id, step, status, message, duration))
                
                conn.commit()
        except Exception as e:
            logger.error(f"처리 로그 기록 실패: {e}")
    
    def check_duplicate_by_content_id(self, content_id: str) -> Optional[str]:
        """Content ID로 중복 문서를 확인합니다."""
        if not content_id:
            return None
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT doc_id FROM papers WHERE content_id = ? AND processing_status = 'completed'
                ''', (content_id,))
                
                row = cursor.fetchone()
                return row['doc_id'] if row else None
        except Exception as e:
            logger.error(f"중복 확인 실패: {e}")
            return None
    
    def get_all_papers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """모든 논문 목록을 조회합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT doc_id, title, authors, publication_year, 
                           processing_status, upload_time, processed_at
                    FROM papers 
                    ORDER BY upload_time DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    result = dict(row)
                    if result.get('authors'):
                        try:
                            result['authors'] = json.loads(result['authors'])
                        except:
                            result['authors'] = []
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"논문 목록 조회 실패: {e}")
            return []