# 📄 Paper Alchemist

과학 논문 PDF 파일을 입력받아 OCR, 품질 평가, 임베딩 생성, 서지정보 추출을 자동으로 수행하는 통합 처리 시스템입니다.

## 🎯 주요 기능

- **OCR 및 품질 평가**: LLaVA를 통한 지능형 OCR 필요성 판단
- **텍스트 임베딩**: BGE-M3 모델을 사용한 벡터 생성
- **서지정보 추출**: LLM 기반 메타데이터 자동 추출
- **내용 기반 중복 검출**: 임베딩 기반 고유 ID 생성
- **SQLite 저장**: 경량 데이터베이스 기반 관리
- **REST API**: FastAPI를 통한 웹 서비스 제공

## 🏗️ 시스템 구조

```
paper-alchemist/
├── docker-compose.yml          # Docker 컨테이너 구성
├── Dockerfile                  # FastAPI 서버 이미지
├── app/
│   ├── main.py                # FastAPI 서버 진입점
│   ├── pipeline.py            # 전체 처리 파이프라인
│   ├── ocr.py                 # OCR 및 텍스트 추출
│   ├── ocr_quality.py         # LLaVA 기반 품질 평가
│   ├── embedding.py           # BGE-M3 임베딩 생성
│   ├── metadata.py            # LLM 서지정보 추출
│   ├── db.py                  # SQLite 데이터베이스
│   └── requirements.txt       # Python 의존성
├── data/                      # 데이터 저장소 (자동 생성)
└── README.md
```

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/paper-alchemist.git
cd paper-alchemist
```

### 2. Docker로 실행
```bash
# 서비스 시작 (Ollama + FastAPI)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. API 테스트
```bash
# 서비스 상태 확인
curl http://localhost:8000/health

# PDF 파일 업로드 및 처리
curl -X POST "http://localhost:8000/process" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_paper.pdf"
```

## 📡 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/` | API 정보 및 엔드포인트 목록 |
| `POST` | `/process` | PDF 업로드 및 자동 처리 |
| `GET` | `/metadata/{doc_id}` | 서지정보 및 OCR 품질 조회 |
| `GET` | `/embedding/{doc_id}` | 벡터 임베딩 조회 |
| `GET` | `/preview/{doc_id}` | 첫 페이지 이미지 미리보기 |
| `GET` | `/status/{doc_id}` | 처리 상태 조회 |
| `GET` | `/papers` | 논문 목록 조회 |
| `GET` | `/health` | 서비스 상태 확인 |

## 🔄 처리 흐름

1. **PDF 업로드** → 파일 저장 및 기본 정보 등록
2. **OCR 처리** → 필요시 ocrmypdf를 통한 텍스트 추출
3. **품질 평가** → LLaVA 모델로 OCR 품질 분석
4. **임베딩 생성** → BGE-M3 모델로 벡터 생성 및 Content ID 계산
5. **메타데이터 추출** → LLM을 통한 서지정보 추출
6. **데이터베이스 저장** → SQLite에 모든 정보 저장

## 🧩 사용 기술

- **FastAPI**: REST API 서버
- **OCRmyPDF**: OCR 처리 엔진
- **Ollama + LLaVA**: OCR 품질 평가
- **BGE-M3**: 다국어 임베딩 모델
- **SQLite**: 경량 데이터베이스
- **Docker**: 컨테이너화 및 배포

## 📋 요구사항

- Docker & Docker Compose
- 최소 4GB RAM (임베딩 모델 로딩)
- 충분한 디스크 공간 (PDF 파일 및 DB 저장)

## 🔧 개발 모드

```bash
# 개발용 실행
cd app
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 환경 변수

- `OLLAMA_BASE_URL`: Ollama 서비스 URL (기본값: http://localhost:11434)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙋‍♂️ 문의

프로젝트 관련 문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해주세요.