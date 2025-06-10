import os
import fitz
import ocrmypdf
from pdf2image import convert_from_path
from pathlib import Path
import tempfile
import base64
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트를 추출합니다."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"텍스트 추출 실패: {e}")
        return ""

def perform_ocr(pdf_path: str, output_path: str = None) -> str:
    """PDF에 OCR을 수행합니다."""
    if output_path is None:
        output_path = pdf_path.replace('.pdf', '_ocr.pdf')
    
    try:
        ocrmypdf.ocr(
            input_file=pdf_path,
            output_file=output_path,
            language=['eng', 'kor'],
            force_ocr=True,
            skip_text=False,
            optimize=1,
            quiet=True
        )
        return output_path
    except Exception as e:
        logger.error(f"OCR 실패: {e}")
        return pdf_path

def extract_first_page_image(pdf_path: str, output_dir: str) -> str:
    """PDF의 첫 페이지를 이미지로 추출합니다."""
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
        if images:
            image_path = os.path.join(output_dir, f"{Path(pdf_path).stem}_page1.png")
            images[0].save(image_path, 'PNG')
            return image_path
    except Exception as e:
        logger.error(f"이미지 추출 실패: {e}")
    return None

def image_to_base64(image_path: str) -> str:
    """이미지를 base64로 인코딩합니다."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Base64 인코딩 실패: {e}")
        return None

def process_pdf_ocr(pdf_path: str, doc_id: str, data_dir: str = "data") -> dict:
    """PDF에 대한 전체 OCR 처리를 수행합니다."""
    result = {
        "doc_id": doc_id,
        "original_text": "",
        "ocr_text": "",
        "ocr_performed": False,
        "first_page_image": None,
        "first_page_base64": None
    }
    
    # 원본 텍스트 추출
    original_text = extract_text_from_pdf(pdf_path)
    result["original_text"] = original_text
    
    # 첫 페이지 이미지 추출
    image_path = extract_first_page_image(pdf_path, data_dir)
    if image_path:
        result["first_page_image"] = image_path
        result["first_page_base64"] = image_to_base64(image_path)
    
    # 텍스트가 거의 없으면 OCR 수행
    if len(original_text.strip()) < 100:
        logger.info("텍스트가 부족하여 OCR을 수행합니다.")
        ocr_pdf_path = os.path.join(data_dir, f"{doc_id}_ocr.pdf")
        ocr_result = perform_ocr(pdf_path, ocr_pdf_path)
        
        if ocr_result != pdf_path:
            ocr_text = extract_text_from_pdf(ocr_result)
            result["ocr_text"] = ocr_text
            result["ocr_performed"] = True
        else:
            result["ocr_text"] = original_text
    else:
        result["ocr_text"] = original_text
    
    return result