from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/platform-accounts", tags=["platform-accounts"])


class PlatformAccountCreate(BaseModel):
    platform: str  # karrot|bunjang|fruits|charan|ebay
    username: str
    password: str  # Secrets Manager에 암호화 저장, 평문은 즉시 폐기


class PlatformAccountOut(BaseModel):
    id: str
    platform: str
    is_active: bool


@router.get("", response_model=list[PlatformAccountOut])
async def list_accounts():
    # TODO: 연동된 플랫폼 계정 목록
    raise NotImplementedError


@router.post("", response_model=PlatformAccountOut, status_code=201)
async def connect_account(body: PlatformAccountCreate):
    # TODO: Secrets Manager에 자격증명 저장 → DB에 key ref 저장
    raise NotImplementedError


@router.delete("/{account_id}", status_code=204)
async def disconnect_account(account_id: str):
    # TODO: Secrets Manager 삭제 → DB 비활성화
    raise NotImplementedError
