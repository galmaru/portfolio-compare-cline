# 📊 포트폴리오 비교 (Portfolio Compare)

한국 주식과 ETF 포트폴리오의 실적을 비교하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **포트폴리오 생성**: 국내 주식/ETF를 검색하여 포트폴리오를 구성
- **비율 설정**: 각 종목별 투자 비율(%) 설정 (합계 100%)
- **기간 설정**: 과거 특정 날짜부터 어제까지의 기간 설정
- **금액 설정**: 만원 단위로 총 투자 금액 설정
- **성과 비교**: 여러 포트폴리오의 수익률을 선형 차트로 비교
- **시각화**: Recharts를 활용한 일별 가치 변화 시각화

## 🛠 기술 스택

### 프론트엔드
- React 18 + TypeScript
- Vite
- Recharts (차트)
- Axios (HTTP 클라이언트)

### 백엔드
- Python FastAPI
- yfinance (한국 주식 데이터)
- SQLAlchemy + SQLite

### 배포
- Vercel

## 📁 프로젝트 구조

```
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── api/           # API 호출 함수
│   │   ├── components/    # React 컴포넌트
│   │   ├── types/         # TypeScript 타입
│   │   ├── App.tsx        # 메인 앱
│   │   └── main.tsx       # 엔트리 포인트
│   ├── package.json
│   └── vite.config.ts
├── backend/               # Python 백엔드 (로컬 개발용)
│   ├── main.py
│   ├── models/
│   ├── services/
│   └── requirements.txt
├── api/                   # Vercel 서버리스 함수
│   ├── index.py
│   └── requirements.txt
└── vercel.json
```

## 🚀 로컬 개발 환경 설정

### 1. 백엔드 실행

```bash
# Python 가상환경 생성 (Python 3.10+ 필요)
cd backend
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
./venv/bin/uvicorn main:app --reload --port 3002
```

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3002` 접속

## 📦 Vercel 배포

1. Vercel 계정 생성 및 GitHub 연동
2. 저장소 import
3. 자동 배포 설정

```bash
# Vercel CLI 설치 (선택사항)
npm i -g vercel

# 배포
vercel
```

## 📊 사용 방법

1. **포트폴리오 생성**: "+ 새 포트폴리오" 버튼 클릭
2. **종목 검색**: 종목명 또는 코드 검색 (예: 삼성전자, 005930)
3. **비율 설정**: 각 종목별 투자 비율 설정 (합계 100%)
4. **기간/금액 설정**: 시작일과 투자 금액 입력
5. **비교 분석**: 포트폴리오 2개 이상 선택 후 "비교 시작" 클릭
6. **결과 확인**: 선형 차트로 수익률/금액 비교

## ⚠️ 주의사항

- yfinance는 Yahoo Finance 데이터를 사용하며, 한국 주식은 `.KS` 티커를 사용합니다
- 주가 데이터는 일별 기준이며, 공휴일/주말은 제외됩니다
- 종료일은 자동으로 어제 날짜로 고정됩니다
- Vercel Hobby 플랜은 서버리스 함수 실행 시간 제한(10초)이 있습니다
- 로컬에서 백엔드 실행 시 Python 3.10+가 필요합니다

## 📝 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/stocks/search?keyword=xxx` | 주식/ETF 검색 |
| POST | `/api/portfolios` | 포트폴리오 생성 |
| GET | `/api/portfolios` | 포트폴리오 목록 |
| GET | `/api/portfolios/{id}` | 포트폴리오 상세 |
| DELETE | `/api/portfolios/{id}` | 포트폴리오 삭제 |
| POST | `/api/compare` | 포트폴리오 비교 분석 |

## 📄 라이선스

MIT