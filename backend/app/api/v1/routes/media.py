"""[윤채린] 이미지/썸네일 처리 엔드포인트."""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.media.thumbnail import make_thumbnail

router = APIRouter(prefix="/media", tags=["media"])


class ThumbnailRequest(BaseModel):
    s3_key: str


class ThumbnailResponse(BaseModel):
    thumbnail_key: str


class BatchThumbnailRequest(BaseModel):
    s3_keys: List[str]


class BatchThumbnailResponse(BaseModel):
    thumbnails: List[ThumbnailResponse]
    failed: List[str]


@router.post("/thumbnail", response_model=ThumbnailResponse)
async def regenerate_thumbnail(req: ThumbnailRequest):
    """단일 이미지 썸네일 재처리."""
    try:
        key = await make_thumbnail(req.s3_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="썸네일 생성 실패") from exc
    return ThumbnailResponse(thumbnail_key=key)


@router.post("/thumbnails/batch", response_model=BatchThumbnailResponse)
async def batch_thumbnails(req: BatchThumbnailRequest):
    """여러 이미지의 썸네일을 일괄 생성한다. 부분 실패 격리."""
    thumbnails: List[ThumbnailResponse] = []
    failed: List[str] = []

    for s3_key in req.s3_keys:
        try:
            thumb_key = await make_thumbnail(s3_key)
            thumbnails.append(ThumbnailResponse(thumbnail_key=thumb_key))
        except Exception:
            failed.append(s3_key)

    return BatchThumbnailResponse(thumbnails=thumbnails, failed=failed)
