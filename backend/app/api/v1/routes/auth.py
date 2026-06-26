"""[여원] Google OAuth 로그인 + JWT 발급.

프론트에서 받은 Google id_token 을 검증하고, 사용자를 upsert(첫 로그인 = 회원가입)한 뒤
자체 JWT 액세스 토큰을 발급한다.
"""

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_google_token(token: str) -> dict:
    """Google id_token 검증 → 클레임(dict). audience = 우리 Client ID."""
    return google_id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.google_client_id
    )


@router.post("/google", response_model=TokenResponse)
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Google id_token 검증 → 사용자 upsert → 자체 JWT 발급."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID 가 설정되지 않았습니다.",
        )

    try:
        info = await asyncio.to_thread(_verify_google_token, body.id_token)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Google 토큰입니다.",
        )

    google_id = info.get("sub")
    email = info.get("email")
    if not google_id or not email:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Google 토큰에 필요한 정보가 없습니다.",
        )

    # upsert: google_id 기준. 첫 로그인이면 생성(회원가입).
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, google_id=google_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(str(user.id))
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """현재 JWT 의 사용자 정보를 반환한다."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
