import os
import uuid
import logging
import time
from pathlib import Path
from typing import Dict, Optional
import tempfile
import shutil

from ocr import process_pdf_ocr
from ocr_quality import assess_ocr_quality, should_perform_ocr
from embedding import process_text_embedding
from metadata import extract_paper_metadata, validate_metadata
from db import PaperDatabase

logger = logging.getLogger(__name__)

class PaperProcessingPipeline:
    def __init__(self, data_dir: str = "data"):
        """파이프라인을 초기화합니다."""
        self.data_dir = data_dir
        self.db = PaperDatabase(os.path.join(data_dir, "papers.db"))
        
        # 데이터 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)
        
        logger.info(f"파이프라인 초기화 완료 - 데이터 디렉토리: {data_dir}")
    
    def save_uploaded_file(self, file_content: bytes, filename: str, doc_id: str) -> str:
        """업로드된 파일을 저장합니다."""
        file_path = os.path.join(self.data_dir, f"{doc_id}_{filename}")
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"파일 저장 완료: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            raise
    
    def process_pdf(self, file_content: bytes, filename: str) -> Dict:
        """PDF 파일의 전체 처리를 수행합니다."""
        doc_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"PDF 처리 시작 - Doc ID: {doc_id}, 파일명: {filename}")
        
        result = {
            "doc_id": doc_id,
            "filename": filename,
            "status": "processing",
            "steps": {},
            "errors": [],
            "total_duration": 0
        }
        
        try:
            # 1. 파일 저장
            step_start = time.time()
            file_path = self.save_uploaded_file(file_content, filename, doc_id)
            file_size = len(file_content)
            
            # DB에 기본 정보 저장
            self.db.save_paper(doc_id, filename, file_size)
            
            step_duration = time.time() - step_start
            result["steps"]["file_save"] = {
                "status": "completed",
                "duration": step_duration,
                "file_path": file_path,
                "file_size": file_size
            }
            self.db.log_processing_step(doc_id, "file_save", "completed", 
                                      f"파일 크기: {file_size} bytes", step_duration)
            
            # 2. OCR 처리
            step_start = time.time()
            logger.info(f"OCR 처리 시작 - {doc_id}")
            
            ocr_result = process_pdf_ocr(file_path, doc_id, self.data_dir)
            self.db.update_ocr_info(doc_id, ocr_result)
            
            step_duration = time.time() - step_start
            result["steps"]["ocr"] = {
                "status": "completed",
                "duration": step_duration,
                "ocr_performed": ocr_result.get("ocr_performed", False),
                "original_text_length": len(ocr_result.get("original_text", "")),
                "ocr_text_length": len(ocr_result.get("ocr_text", ""))
            }
            self.db.log_processing_step(doc_id, "ocr", "completed", 
                                      f"OCR 수행: {ocr_result.get('ocr_performed')}", step_duration)
            
            # 3. OCR 품질 평가
            step_start = time.time()
            logger.info(f"OCR 품질 평가 시작 - {doc_id}")
            
            quality_assessment = None
            if ocr_result.get("first_page_base64"):
                quality_assessment = assess_ocr_quality(
                    ocr_result["first_page_base64"],
                    ocr_result.get("ocr_text", "")
                )
                self.db.save_ocr_quality(doc_id, quality_assessment)
            
            step_duration = time.time() - step_start
            result["steps"]["quality_assessment"] = {
                "status": "completed" if quality_assessment else "skipped",
                "duration": step_duration,
                "overall_quality": quality_assessment.get("overall_quality") if quality_assessment else None
            }
            self.db.log_processing_step(
                doc_id, "quality_assessment", 
                "completed" if quality_assessment else "skipped",
                f"품질: {quality_assessment.get('overall_quality') if quality_assessment else 'N/A'}", 
                step_duration
            )
            
            # 4. 임베딩 생성
            step_start = time.time()
            logger.info(f"임베딩 생성 시작 - {doc_id}")
            
            # 최종 텍스트 선택 (OCR 수행했으면 OCR 텍스트, 아니면 원본 텍스트)
            final_text = ocr_result.get("ocr_text", "") or ocr_result.get("original_text", "")
            
            embedding_result = process_text_embedding(final_text)
            
            if embedding_result.get("embedding"):
                self.db.save_embedding(doc_id, embedding_result["embedding"], embedding_result)
                
                # 중복 문서 확인
                content_id = embedding_result.get("content_id")
                if content_id:
                    existing_doc = self.db.check_duplicate_by_content_id(content_id)
                    if existing_doc and existing_doc != doc_id:
                        logger.warning(f"중복 문서 발견: {existing_doc}")
                        result["duplicate_doc_id"] = existing_doc
            
            step_duration = time.time() - step_start
            result["steps"]["embedding"] = {
                "status": "completed" if embedding_result.get("embedding") else "failed",
                "duration": step_duration,
                "embedding_dim": embedding_result.get("embedding_dim", 0),
                "chunk_count": embedding_result.get("chunk_count", 0),
                "content_id": embedding_result.get("content_id")
            }
            self.db.log_processing_step(
                doc_id, "embedding", 
                "completed" if embedding_result.get("embedding") else "failed",
                f"차원: {embedding_result.get('embedding_dim')}, 청크: {embedding_result.get('chunk_count')}", 
                step_duration
            )
            
            # 5. 메타데이터 추출
            step_start = time.time()
            logger.info(f"메타데이터 추출 시작 - {doc_id}")
            
            metadata = extract_paper_metadata(final_text)
            validated_metadata = validate_metadata(metadata)
            self.db.save_metadata(doc_id, validated_metadata)
            
            step_duration = time.time() - step_start
            result["steps"]["metadata"] = {
                "status": "completed",
                "duration": step_duration,
                "title": validated_metadata.get("title"),
                "authors_count": len(validated_metadata.get("authors", [])),
                "extraction_method": validated_metadata.get("extraction_method"),
                "llm_available": validated_metadata.get("llm_available", False)
            }
            self.db.log_processing_step(
                doc_id, "metadata", "completed",
                f"제목: {validated_metadata.get('title', 'N/A')[:50]}", 
                step_duration
            )
            
            # 6. 처리 완료
            self.db.complete_processing(doc_id)
            
            total_duration = time.time() - start_time
            result["status"] = "completed"
            result["total_duration"] = total_duration
            
            logger.info(f"PDF 처리 완료 - {doc_id} ({total_duration:.2f}초)")
            
            # 임시 파일 정리
            self._cleanup_temp_files(doc_id)
            
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생 - {doc_id}: {e}")
            result["status"] = "failed"
            result["errors"].append(str(e))
            result["total_duration"] = time.time() - start_time
            
            self.db.log_processing_step(doc_id, "pipeline", "failed", str(e))
            
            # 실패시에도 임시 파일 정리
            self._cleanup_temp_files(doc_id)
        
        return result
    
    def _cleanup_temp_files(self, doc_id: str):
        """임시 파일들을 정리합니다."""
        try:
            # OCR 결과 파일 정리
            temp_files = [
                os.path.join(self.data_dir, f"{doc_id}_ocr.pdf"),
                # 필요에 따라 다른 임시 파일들 추가
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"임시 파일 삭제: {temp_file}")
                    
        except Exception as e:
            logger.warning(f"임시 파일 정리 중 오류: {e}")
    
    def get_processing_status(self, doc_id: str) -> Optional[Dict]:
        """처리 상태를 조회합니다."""
        try:
            paper_info = self.db.get_paper_metadata(doc_id)
            if not paper_info:
                return None
            
            return {
                "doc_id": doc_id,
                "status": paper_info.get("processing_status"),
                "filename": paper_info.get("filename"),
                "upload_time": paper_info.get("upload_time"),
                "processed_at": paper_info.get("processed_at"),
                "title": paper_info.get("title"),
                "authors": paper_info.get("authors", []),
                "ocr_performed": paper_info.get("ocr_performed", False),
                "embedding_dim": paper_info.get("embedding_dim", 0)
            }
        except Exception as e:
            logger.error(f"처리 상태 조회 실패: {e}")
            return None
    
    def get_first_page_image_path(self, doc_id: str) -> Optional[str]:
        """첫 페이지 이미지 경로를 반환합니다."""
        try:
            image_path = os.path.join(self.data_dir, f"{doc_id}_page1.png")
            return image_path if os.path.exists(image_path) else None
        except Exception as e:
            logger.error(f"이미지 경로 조회 실패: {e}")
            return None

def create_pipeline(data_dir: str = "data") -> PaperProcessingPipeline:
    """파이프라인 인스턴스를 생성합니다."""
    return PaperProcessingPipeline(data_dir)