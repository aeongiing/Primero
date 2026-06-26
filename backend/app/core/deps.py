"""[여원] 공통 FastAPI 의존성.

DB 세션과 현재 인증 사용자를 주입하는 의존성을 제공한다.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> uuid.UUID:
    """Authorization 헤더의 JWT 를 검증해 사용자 ID 를 반환한다."""
    try:
        payload = decode_access_token(credentials.credentials)
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


__all__ = ["get_db", "get_current_user_id", "AsyncSession"]
