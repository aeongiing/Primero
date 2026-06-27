from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

DESCRIPTION = """
**파라파라(ParaPara)** — 빈티지·중고 의류 멀티 플랫폼 업로드 자동화 API.

파라파라에 상품을 한 번 등록하면 번개장터·차란·당근·ebay 등에 자동 등록·동기화한다.
`표준_상품(Canonical Product)`이 유일한 원본(SSOT)이며 모든 플랫폼 등록물은 이로부터 복제된다.

### 핵심 플로우
업로드 → AI 분석(카테고리·색상)·설명 생성 → 사진 정렬/보정 → 표준_상품 저장
→ 플랫폼 매핑 → OpenClaw 발행 → 판매 동기화/미판매 할인.

### 메타데이터
`/api/v1/metadata` 엔드포인트가 플랫폼 입력 폼에 필요한 정규 옵션과
플랫폼별 카테고리 트리를 제공한다 (SSOT: `플랫폼 input.md`, 정규값은 차란 기준).
"""

tags_metadata = [
    {"name": "metadata", "description": "플랫폼 입력 옵션·카테고리 트리 (업로드 폼 구성용)."},
    {"name": "products", "description": "표준_상품 등록·조회·수정·삭제 및 AI 이미지 분석."},
    {"name": "listings", "description": "상품의 플랫폼별 등록 현황·판매 동기화."},
    {"name": "platform-accounts", "description": "플랫폼 계정 연동(자격증명은 시크릿 저장)."},
    {"name": "auth", "description": "Google OAuth 로그인 및 사용자 정보."},
]

app = FastAPI(
    title="ParaPara API",
    version="0.1.0",
    description=DESCRIPTION,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "ParaPara"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://100.53.237.32:3000",  # 팀 내부 서버
        "https://paraparavintage.vercel.app",  # Vercel 프로덕션
        "https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app",  # Vercel Preview
        "https://parapara-vintage.vercel.app",  # Vercel alias
    ],
    allow_origin_regex=r"(http://localhost:\d+|https://.*\.vercel\.app|https://.*\.ngrok-free\.app|https://.*\.ngrok-free\.dev|https://.*\.trycloudflare\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"], summary="헬스체크")
async def health():
    return {"status": "ok"}
