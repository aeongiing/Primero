"""[윤채린] 썸네일 누끼 + 보정 처리.

rembg(U^2-Net)로 배경 제거 후 Pillow로 흰 배경 합성·밝기/대비 보정·
정사각 썸네일 리사이즈를 수행한다.
rembg 미설치 환경에서는 배경 제거를 건너뛰고 보정만 적용한다.
"""

import asyncio
import io
from functools import lru_cache

import boto3
from PIL import Image, ImageEnhance

from app.core.config import settings

try:
    from rembg import remove as rembg_remove
    _HAS_REMBG = True
except ImportError:
    _HAS_REMBG = False

THUMB_SIZE = (1000, 1000)


@lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def _thumb_key(s3_key: str) -> str:
    """원본 key에서 썸네일 key 생성. e.g. .../0.jpg → .../0_thumb.jpg"""
    dot = s3_key.rfind(".")
    if dot == -1:
        return f"{s3_key}_thumb"
    return f"{s3_key[:dot]}_thumb{s3_key[dot:]}"


def _process(image_bytes: bytes) -> bytes:
    # 1. 배경 제거 (rembg 있을 때만)
    if _HAS_REMBG:
        fg_bytes = rembg_remove(image_bytes)
        fg = Image.open(io.BytesIO(fg_bytes)).convert("RGBA")
    else:
        fg = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # 2. 흰 배경 위에 중앙 배치
    bg = Image.new("RGBA", THUMB_SIZE, (255, 255, 255, 255))
    fg.thumbnail(THUMB_SIZE, Image.LANCZOS)
    offset = ((THUMB_SIZE[0] - fg.width) // 2, (THUMB_SIZE[1] - fg.height) // 2)
    bg.paste(fg, offset, fg)

    # 3. RGB 변환 후 보정
    img = bg.convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Contrast(img).enhance(1.1)

    # 4. JPEG 저장
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _download_and_upload(s3_key: str) -> str:
    obj = _client().get_object(Bucket=settings.s3_bucket, Key=s3_key)
    image_bytes = obj["Body"].read()

    thumb_bytes = _process(image_bytes)
    thumb_key = _thumb_key(s3_key)

    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=thumb_key,
        Body=thumb_bytes,
        ContentType="image/jpeg",
    )
    return thumb_key


async def make_thumbnail(s3_key: str) -> str:
    """원본 이미지에서 누끼+보정된 썸네일을 생성해 S3 key를 반환한다."""
    return await asyncio.to_thread(_download_and_upload, s3_key)
