"""[윤채린] 사진 업로드 → S3 저장.

업로드 파일을 S3에 저장하고 key 를 반환한다. key 규칙은
`{user_id}/{product_id}/{order}.jpg` 를 따른다.

boto3 는 동기 클라이언트이므로, 비동기 핸들러에서 이벤트 루프를 막지
않도록 blocking I/O 는 asyncio.to_thread 로 감싼다.
"""

from __future__ import annotations

import asyncio
import uuid
from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings

# 허용 입력 형식과 최대 용량 (요구사항: JPEG/PNG, 10MB)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_BYTES = 10 * 1024 * 1024


class UploadValidationError(Exception):
    """업로드 입력 검증 실패 (형식/용량)."""


class S3StorageError(Exception):
    """S3 저장 실패."""


@lru_cache(maxsize=1)
def _client():
    """프로세스 단위로 재사용하는 S3 클라이언트."""
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def build_key(user_id: uuid.UUID, product_id: uuid.UUID, order: int) -> str:
    """S3 객체 key 생성 규칙."""
    return f"{user_id}/{product_id}/{order}.jpg"


def _validate(content_type: str | None, size: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError(
            f"지원하지 않는 형식입니다. 허용: {sorted(ALLOWED_CONTENT_TYPES)}"
        )
    if size > MAX_FILE_BYTES:
        raise UploadValidationError("파일 크기가 최대 허용치(10MB)를 초과했습니다.")


def _put_object(key: str, body: bytes, content_type: str) -> None:
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
    )


async def upload(file: UploadFile, key: str) -> str:
    """파일을 S3 버킷에 업로드하고 저장된 key 를 반환한다.

    Raises:
        UploadValidationError: 형식/용량 검증 실패.
        S3StorageError: S3 저장 실패.
    """
    body = await file.read()
    _validate(file.content_type, len(body))
    try:
        await asyncio.to_thread(_put_object, key, body, file.content_type)
    except (BotoCoreError, ClientError) as exc:
        # 키 값 등 시크릿은 메시지에 넣지 않는다.
        raise S3StorageError(f"S3 저장에 실패했습니다 (key={key})") from exc
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """S3 객체의 presigned URL을 반환한다 (기본 1시간).

    버킷/키가 없거나 오류 시 빈 문자열을 반환한다.
    """
    if not settings.s3_bucket or not key:
        return ""
    try:
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError):
        return ""


async def head_bucket() -> bool:
    """버킷 연결 확인용 헬스체크. 접근 가능하면 True."""
    try:
        await asyncio.to_thread(_client().head_bucket, Bucket=settings.s3_bucket)
        return True
    except (BotoCoreError, ClientError):
        return False
