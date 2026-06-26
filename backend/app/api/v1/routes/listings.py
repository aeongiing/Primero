"""[여원] 리스팅(플랫폼별 등록물) 조회 라우트.

리스팅은 표준_상품으로부터 파생된 플랫폼별 등록물이다. 여기서는 상품의
플랫폼별 등록 현황을 조회한다. 판매완료 전파(작업 8)는 자동화 레이어 책임이다.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user_id
from app.models.product import Product
from app.models.listing import Listing
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/{product_id}", response_model=list[ListingOut])
async def get_listings(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """상품의 플랫폼별 등록 현황을 반환한다.

    상품 소유자만 조회할 수 있다. 소유하지 않거나 존재하지 않으면 404.
    """
    owner = await db.execute(
        select(Product.id).where(Product.id == product_id, Product.user_id == user_id)
    )
    if owner.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    result = await db.execute(
        select(Listing).where(Listing.product_id == product_id).order_by(Listing.listed_at)
    )
    return list(result.scalars().all())


@router.post("/{listing_id}/sold", status_code=200)
async def mark_sold(listing_id: uuid.UUID):
    # 담당: 작업 8 (판매 완료 폴링 + 자동 삭제) — sold_sync.sync_sold 트리거
    raise NotImplementedError
