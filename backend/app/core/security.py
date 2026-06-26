"""[여원] JWT 발급/검증.

Google OAuth 로그인 성공 시 자체 JWT 를 발급하고, 요청마다 검증한다.
"""

from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings


def create_access_token(subject: str) -> str:
    """사용자 식별자로 JWT 액세스 토큰을 발급한다."""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """JWT 를 검증하고 payload 를 반환한다."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
