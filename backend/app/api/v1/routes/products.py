import uuid

from fastapi import APIRouter, UploadFile, File, Form

from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.schemas.ai import AIAnalysisResult

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/analyze", response_model=AIAnalysisResult)
async def analyze_images(images: list[UploadFile] = File(...)):
    # TODO: S3 업로드 → Rekognition 분석 → Bedrock 설명 생성
    raise NotImplementedError


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate):
    # TODO: DB 저장 → SQS로 플랫폼 등록 태스크 발행
    raise NotImplementedError


@router.get("", response_model=list[ProductOut])
async def list_products(status: str | None = None):
    # TODO: 현재 사용자의 상품 목록 반환
    raise NotImplementedError


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID):
    # TODO: 상품 상세 + 리스팅 상태 반환
    raise NotImplementedError


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: uuid.UUID, body: ProductUpdate):
    # TODO: 가격/설명 수정 → 연동 플랫폼 일괄 반영
    raise NotImplementedError


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: uuid.UUID):
    # TODO: 모든 플랫폼에서 삭제
    raise NotImplementedError
