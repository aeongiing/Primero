"""AWS Secrets Manager 클라이언트.

플랫폼 자격증명을 안전하게 로드한다.
"""

import asyncio
import json
import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.platform.browser import Credentials

logger = logging.getLogger(__name__)


class SecretsManagerError(Exception):
    """Secrets Manager 오류."""


@lru_cache(maxsize=1)
def _client():
    """Secrets Manager 클라이언트 (프로세스 단위 재사용)."""
    return boto3.client(
        "secretsmanager",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


async def load_credentials(credential_key: str) -> Credentials:
    """Secrets Manager에서 자격증명을 로드한다.
    
    Args:
        credential_key: Secrets Manager 키 (예: parapara/platform/user123/bunjang)
    
    Returns:
        Credentials: 플랫폼 로그인 자격증명
    
    Raises:
        SecretsManagerError: 조회 실패 또는 형식 오류
    """
    try:
        # boto3는 동기이므로 to_thread로 감싸기
        response = await asyncio.to_thread(
            _client().get_secret_value,
            SecretId=credential_key
        )
        secret_string = response.get("SecretString")
        
        if not secret_string:
            raise SecretsManagerError(f"Secret {credential_key} has no value")
        
        data = json.loads(secret_string)
        
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            raise SecretsManagerError(f"Secret {credential_key} missing username or password")
        
        return Credentials(username=username, password=password)
    
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        
        # 비밀 정보 보호: credential_key만 로그에 기록
        logger.error(f"Failed to load credentials: key={credential_key}, error_code={error_code}")
        
        if error_code == "ResourceNotFoundException":
            raise SecretsManagerError(f"Secret not found: {credential_key}") from e
        elif error_code == "AccessDeniedException":
            raise SecretsManagerError(f"Access denied to secret: {credential_key}") from e
        else:
            raise SecretsManagerError(f"Failed to load secret {credential_key}: {error_code}") from e
    
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Invalid secret format: key={credential_key}")
        raise SecretsManagerError(f"Invalid secret format for {credential_key}") from e
