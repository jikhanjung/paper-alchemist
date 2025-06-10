#!/usr/bin/env python3
"""
Paper Alchemist API 클라이언트 테스트 프로그램
"""

import requests
import json
import os
import time
import argparse
from pathlib import Path
from typing import Dict, Any

class PaperAlchemistClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        
    def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_api_info(self) -> Dict[str, Any]:
        """API 정보 조회"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def upload_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일 업로드 및 처리"""
        if not os.path.exists(pdf_path):
            return {"error": f"파일을 찾을 수 없습니다: {pdf_path}"}
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                response = requests.post(f"{self.base_url}/process", files=files)
                return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_metadata(self, doc_id: str) -> Dict[str, Any]:
        """메타데이터 조회"""
        try:
            response = requests.get(f"{self.base_url}/metadata/{doc_id}")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_embedding(self, doc_id: str) -> Dict[str, Any]:
        """임베딩 조회"""
        try:
            response = requests.get(f"{self.base_url}/embedding/{doc_id}")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_preview(self, doc_id: str, save_path: str = None) -> bool:
        """미리보기 이미지 다운로드"""
        try:
            response = requests.get(f"{self.base_url}/preview/{doc_id}")
            
            if response.status_code == 200:
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    print(f"미리보기 이미지 저장: {save_path}")
                return True
            else:
                print(f"미리보기 이미지 조회 실패: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"미리보기 이미지 조회 오류: {e}")
            return False
    
    def get_papers(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """논문 목록 조회"""
        try:
            response = requests.get(f"{self.base_url}/papers", 
                                  params={"limit": limit, "offset": offset})
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_status(self, doc_id: str) -> Dict[str, Any]:
        """처리 상태 조회"""
        try:
            response = requests.get(f"{self.base_url}/status/{doc_id}")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

def print_json(data: Dict[str, Any], title: str = ""):
    """JSON 데이터를 예쁘게 출력"""
    if title:
        print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Paper Alchemist API 테스트 클라이언트")
    parser.add_argument("--url", default="http://localhost:8000", help="API 서버 URL")
    parser.add_argument("--pdf", help="테스트할 PDF 파일 경로")
    parser.add_argument("--doc-id", help="조회할 문서 ID")
    parser.add_argument("--action", choices=["health", "info", "upload", "metadata", 
                       "embedding", "preview", "papers", "status", "all"], 
                       default="all", help="실행할 작업")
    
    args = parser.parse_args()
    
    client = PaperAlchemistClient(args.url)
    
    print(f"Paper Alchemist API 테스트 클라이언트")
    print(f"서버 URL: {args.url}")
    print("=" * 50)
    
    if args.action in ["health", "all"]:
        print_json(client.health_check(), "서버 상태 확인")
    
    if args.action in ["info", "all"]:
        print_json(client.get_api_info(), "API 정보")
    
    if args.action in ["papers", "all"]:
        print_json(client.get_papers(), "논문 목록")
    
    if args.action == "upload" and args.pdf:
        print(f"\nPDF 업로드 중: {args.pdf}")
        result = client.upload_pdf(args.pdf)
        print_json(result, "PDF 처리 결과")
        
        if "doc_id" in result:
            doc_id = result["doc_id"]
            print(f"\n생성된 문서 ID: {doc_id}")
            
            # 메타데이터 조회
            print_json(client.get_metadata(doc_id), "메타데이터")
            
            # 임베딩 조회 (크기만 확인)
            embedding_result = client.get_embedding(doc_id)
            if "embedding" in embedding_result:
                embedding_result["embedding"] = f"[{len(embedding_result['embedding'])}개 요소]"
            print_json(embedding_result, "임베딩 정보")
            
            # 미리보기 이미지 다운로드
            preview_path = f"preview_{doc_id}.png"
            if client.get_preview(doc_id, preview_path):
                print(f"미리보기 이미지 저장됨: {preview_path}")
    
    if args.action in ["metadata", "embedding", "status", "preview"] and args.doc_id:
        if args.action == "metadata":
            print_json(client.get_metadata(args.doc_id), "메타데이터")
        elif args.action == "embedding":
            result = client.get_embedding(args.doc_id)
            if "embedding" in result:
                result["embedding"] = f"[{len(result['embedding'])}개 요소]"
            print_json(result, "임베딩 정보")
        elif args.action == "status":
            print_json(client.get_status(args.doc_id), "처리 상태")
        elif args.action == "preview":
            preview_path = f"preview_{args.doc_id}.png"
            client.get_preview(args.doc_id, preview_path)
    
    print("\n" + "=" * 50)
    print("테스트 완료")

if __name__ == "__main__":
    main()