from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
import logging
import os
from typing import Dict, List, Optional
import mimetypes

from pipeline import create_pipeline
from db import PaperDatabase

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Paper Alchemist API",
    description="과학 논문 PDF 통합 처리 시스템",
    version="1.0.0"
)

# 전역 변수
pipeline = None
db = None

@app.on_event("startup")
async def startup_event():
    """서버 시작시 초기화"""
    global pipeline, db
    
    try:
        # 데이터 디렉토리 생성
        os.makedirs("data", exist_ok=True)
        
        # 파이프라인과 DB 초기화
        pipeline = create_pipeline("data")
        db = PaperDatabase("data/papers.db")
        
        logger.info("Paper Alchemist API 서버 시작 완료")
        
    except Exception as e:
        logger.error(f"서버 초기화 실패: {e}")
        raise

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "service": "Paper Alchemist",
        "version": "1.0.0",
        "description": "과학 논문 PDF 통합 처리 시스템",
        "endpoints": {
            "POST /process": "PDF 업로드 및 자동 처리",
            "GET /metadata/{doc_id}": "서지정보 및 OCR 품질 조회",
            "GET /embedding/{doc_id}": "벡터 임베딩 조회",
            "GET /preview/{doc_id}": "첫 페이지 이미지 미리보기",
            "GET /status/{doc_id}": "처리 상태 조회",
            "GET /papers": "논문 목록 조회"
        }
    }

@app.post("/process")
async def process_pdf(file: UploadFile = File(...)):
    """PDF 파일을 업로드하고 전체 처리를 수행합니다."""
    
    # 파일 형식 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    try:
        # 파일 내용 읽기
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB 제한
            raise HTTPException(status_code=400, detail="파일 크기가 50MB를 초과합니다.")
        
        logger.info(f"PDF 처리 요청: {file.filename} ({len(file_content)} bytes)")
        
        # 파이프라인 처리
        result = pipeline.process_pdf(file_content, file.filename)
        
        return {
            "message": "PDF 처리가 완료되었습니다.",
            "doc_id": result["doc_id"],
            "filename": result["filename"],
            "status": result["status"],
            "processing_time": f"{result['total_duration']:.2f}초",
            "steps": result["steps"],
            "duplicate_doc_id": result.get("duplicate_doc_id"),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        logger.error(f"PDF 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/metadata/{doc_id}")
async def get_metadata(doc_id: str):
    """논문의 서지정보와 OCR 품질 정보를 조회합니다."""
    
    try:
        metadata = db.get_paper_metadata(doc_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        # OCR 품질 정보와 메타데이터 분리
        ocr_quality = {}
        paper_metadata = {}
        
        for key, value in metadata.items():
            if key.startswith(('text_clarity', 'layout_complexity', 'image_quality', 
                             'language_mix', 'overall_quality', 'confidence_score', 
                             'recommendations', 'service_available', 'assessed_at')):
                if value is not None:
                    ocr_quality[key] = value
            else:
                paper_metadata[key] = value
        
        return {
            "doc_id": doc_id,
            "paper_metadata": paper_metadata,
            "ocr_quality": ocr_quality if ocr_quality else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메타데이터 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="메타데이터 조회 중 오류가 발생했습니다.")

@app.get("/embedding/{doc_id}")
async def get_embedding(doc_id: str):
    """논문의 벡터 임베딩을 조회합니다."""
    
    try:
        embedding = db.get_embedding(doc_id)
        
        if not embedding:
            raise HTTPException(status_code=404, detail="임베딩을 찾을 수 없습니다.")
        
        return {
            "doc_id": doc_id,
            "embedding": embedding,
            "dimension": len(embedding)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"임베딩 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="임베딩 조회 중 오류가 발생했습니다.")

@app.get("/preview/{doc_id}")
async def get_preview_image(doc_id: str):
    """논문의 첫 페이지 이미지를 반환합니다."""
    
    try:
        image_path = pipeline.get_first_page_image_path(doc_id)
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="미리보기 이미지를 찾을 수 없습니다.")
        
        # MIME 타입 추론
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/png"
        
        return FileResponse(
            path=image_path,
            media_type=mime_type,
            filename=f"{doc_id}_preview.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"미리보기 이미지 제공 중 오류: {e}")
        raise HTTPException(status_code=500, detail="이미지 제공 중 오류가 발생했습니다.")

@app.get("/status/{doc_id}")
async def get_processing_status(doc_id: str):
    """문서의 처리 상태를 조회합니다."""
    
    try:
        status = pipeline.get_processing_status(doc_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상태 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="상태 조회 중 오류가 발생했습니다.")

@app.get("/papers")
async def get_papers(limit: int = 20, offset: int = 0):
    """논문 목록을 조회합니다."""
    
    try:
        if limit > 100:
            limit = 100
        
        papers = db.get_all_papers(limit=limit, offset=offset)
        
        return {
            "papers": papers,
            "count": len(papers),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"논문 목록 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="논문 목록 조회 중 오류가 발생했습니다.")

@app.get("/health")
async def health_check():
    """서비스 상태를 확인합니다."""
    
    try:
        # 데이터베이스 연결 테스트
        test_papers = db.get_all_papers(limit=1)
        
        # Ollama 서비스 상태 확인
        from ocr_quality import OllamaClient
        ollama_client = OllamaClient()
        ollama_available = ollama_client.is_available()
        
        return {
            "status": "healthy",
            "database": "connected",
            "ollama_service": "available" if ollama_available else "unavailable",
            "data_directory": os.path.exists("data")
        }
        
    except Exception as e:
        logger.error(f"헬스체크 중 오류: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# 예외 처리
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "요청한 리소스를 찾을 수 없습니다."}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"내부 서버 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)