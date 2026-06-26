# Primero

중고 의류 통합 자동 판매 서비스 — netzero 해커톤

사진 한 장 업로드 → AI 분석 → 당근마켓·번개장터·Fruits·차란·eBay 동시 등록 → 한 플랫폼에서 팔리면 나머지 자동 삭제

## 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Backend**: 별도 레포 (AWS 기반)

## 주요 기능

| 기능 | 설명 |
|------|------|
| 사진 정렬 업로드 | 앞 → 확대 → 뒤 → 디테일 → 오염 → 태그 순 |
| AI 상품 분석 | AWS Rekognition + Bedrock(Claude)으로 카테고리·색상·설명 자동 생성 |
| 썸네일 보정 | 누끼 + 보정 자동 처리 |
| 컨디션 설정 | 1~10점 슬라이더로 상태 등급 입력 |
| 멀티 플랫폼 등록 | 당근·번개·Fruits·차란·eBay 동시 등록 (OpenClaw 기반) |
| 판매 완료 동기화 | 한 플랫폼 판매 완료 시 나머지 플랫폼 자동 삭제 |
| 자동 할인 | 1주일 미판매 시 10% 자동 할인 |

## 페이지 구조

```
/              홈
/upload        상품 등록 (사진 업로드 → AI 분석 → 플랫폼 선택)
/products      내 상품 목록
/products/[id] 상품 상세 (플랫폼별 등록 URL, 판매 상태)
/dashboard     대시보드 (판매 통계)
/settings      설정 (플랫폼 계정 연동)
```

## ERD 요약

```
users ─── products ─── product_images
  │            │
  │         listings ─── sales
  │
platform_accounts
```

## 시작하기

```bash
npm install
npm run dev
```

## 환경 변수

```env
NEXT_PUBLIC_API_URL=   # 백엔드 API 주소
```

## 백엔드 (FastAPI)

`backend/` 에 FastAPI 서버가 있습니다. Swagger 문서는 자동 생성됩니다.

### 로컬 실행

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 플랫폼 메타데이터 API: http://localhost:8000/api/v1/metadata/options

### 배포 (Render)

`render.yaml` Blueprint가 포함돼 있습니다.

1. GitHub에 푸시
2. Render 대시보드 → **New > Blueprint** → 이 레포 연결
3. `render.yaml` 자동 인식 → 대시보드에서 시크릿 환경변수(`DATABASE_URL`, AWS 키 등) 입력
4. 배포 완료 후 공개 URL의 `/docs` 를 팀원에게 공유

`JWT_SECRET`은 Render가 자동 생성하며, 비밀 값은 소스에 평문으로 두지 않습니다(`.env.example`만 커밋).

> 향후 정식 운영은 AWS(ECS Fargate / Lambda + API Gateway, RDS Aurora, S3, Rekognition, Bedrock)로 이전합니다.

## 커밋 규칙

Conventional Commits 기반. 타입은 영어, 내용은 한국어로 작성합니다.

```
feat: 새 기능 추가
fix: 버그 수정
chore: 빌드, 패키지, 설정 변경 (코드 변경 없음)
style: 포맷, 세미콜론 등 스타일 변경 (로직 변경 없음)
refactor: 기능 변경 없는 코드 구조 개선
docs: 문서 수정
test: 테스트 추가 또는 수정
```

예시

```
feat: 상품 업로드 사진 정렬 기능 추가
fix: 판매 완료 시 타 플랫폼 삭제 안 되던 버그 수정
chore: shadcn/ui 버튼 컴포넌트 설치
style: 대시보드 카드 간격 조정
refactor: 플랫폼 등록 로직 서비스 레이어로 분리
docs: 커밋 규칙 README에 추가
```
