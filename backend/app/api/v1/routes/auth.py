from fastapi import APIRouter

from app.schemas.auth import GoogleLoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest):
    # TODO: Google id_token 검증 → DB upsert → JWT 발급
    raise NotImplementedError


@router.get("/me", response_model=UserOut)
async def get_me():
    # TODO: JWT 검증 → 사용자 반환
    raise NotImplementedError
