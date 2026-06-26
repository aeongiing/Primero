"""[여원] 상품(표준_상품) CRUD 라우트.

표준_상품(Canonical Product)은 파라파라의 유일한 원본(SSOT)이다. 이 라우트는
상품의 생성/조회/수정/삭제를 DB 기준으로 처리한다. 플랫폼 발행·삭제(OpenClaw)
같은 외부 전파는 자동화 레이어(작업 7·8)의 책임이며 여기서는 훅으로만 표시한다.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_user_id
from app.domain.mapping.config import ACTIVE_PLATFORMS
from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.schemas.ai import AIAnalysisResult

router = APIRouter(prefix="/products", tags=["products"])


async def _get_owned_product(
    product_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Product:
    """현재 사용자가 소유한 상품을 이미지와 함께 조회한다. 없으면 404."""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.user_id == user_id)
        .options(selectinload(Product.images))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.post("/analyze", response_model=AIAnalysisResult)
async def analyze_images(images: list[UploadFile] = File(...)):
    # 담당: 백엔드 A (윤채린) — S3 업로드 → Rekognition 분석 → Claude 설명 생성
    raise NotImplementedError


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """표준_상품을 생성해 DB 에 저장한다(상태: draft).

    플랫폼 등록 태스크 발행(작업 7)은 별도 단계이며, 인프라(SQS) 준비 후
    publisher.publish_listing_tasks 로 연결한다. 여기서는 SSOT 저장만 책임진다.
    """
    invalid = [p for p in body.platforms if p not in ACTIVE_PLATFORMS]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=(
                f"지원하지 않는 플랫폼: {invalid}. "
                f"현재 등록 가능: {list(ACTIVE_PLATFORMS)}"
            ),
        )

    product = Product(
        user_id=user_id,
        title=body.title,
        brand=body.brand,
        description=body.description,
        category=body.category,
        condition=body.condition,
        price=body.price,
        colors=body.colors,
        materials=body.materials,
        size=body.size,
        chest=body.chest,
        total_length=body.total_length,
        waist=body.waist,
        hip=body.hip,
        rise=body.rise,
        status=ProductStatus.draft,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product, attribute_names=["images"])

    # TODO(작업 7): body.platforms 로 publisher.publish_listing_tasks 발행 (SQS)
    return product


@router.get("", response_model=list[ProductOut])
async def list_products(
    status: ProductStatus | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """현재 사용자의 상품 목록을 반환한다. status 로 필터링 가능."""
    query = (
        select(Product)
        .where(Product.user_id == user_id)
        .options(selectinload(Product.images))
        .order_by(Product.created_at.desc())
    )
    if status is not None:
        query = query.where(Product.status == status)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """상품 상세를 반환한다(이미지 포함)."""
    return await _get_owned_product(product_id, user_id, db)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """가격/설명/제목/컨디션을 수정한다.

    연동된 플랫폼으로의 일괄 반영(작업 7)은 자동화 레이어 책임이며, 여기서는
    표준_상품(SSOT)만 갱신한다.
    """
    product = await _get_owned_product(product_id, user_id, db)

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product, attribute_names=["images"])

    # TODO(작업 7): 변경된 가격/설명을 active 리스팅에 어댑터로 일괄 반영
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """상품을 삭제한다.

    플랫폼 측 리스팅 삭제(작업 8)는 자동화 레이어 책임이다. 여기서는 표준_상품과
    그에 종속된 DB 레코드만 제거한다.
    """
    product = await _get_owned_product(product_id, user_id, db)

    # TODO(작업 8): 삭제 전 active 리스팅을 어댑터로 플랫폼에서 내림 처리
    await db.delete(product)
    await db.commit()
    return None
