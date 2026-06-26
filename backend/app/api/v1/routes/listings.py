import uuid

from fastapi import APIRouter

from app.schemas.listing import ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/{product_id}", response_model=list[ListingOut])
async def get_listings(product_id: uuid.UUID):
    # TODO: 상품의 플랫폼별 등록 현황 반환
    raise NotImplementedError


@router.post("/{listing_id}/sold", status_code=200)
async def mark_sold(listing_id: uuid.UUID):
    # TODO: 수동 판매완료 처리 → 나머지 플랫폼 자동 삭제 트리거
    raise NotImplementedError
