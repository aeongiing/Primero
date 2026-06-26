"""[윤채린] 이미지/썸네일 처리 엔드포인트(선택).

상품 분석과 별개로 단일 이미지 누끼/보정을 재처리할 때 사용한다.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/thumbnail")
async def regenerate_thumbnail(s3_key: str):
    # TODO: services.media.thumbnail.make_thumbnail 호출
    raise NotImplementedError
