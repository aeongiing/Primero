"""[여원] 플랫폼 계정 연동 API.

사용자가 번개장터/중고나라 등 외부 플랫폼에 로그인한 세션을 저장/조회/삭제한다.
세션은 사용자별로 DB에 연동 레코드를 만들고, 실제 세션 데이터(쿠키/토큰)는
서버 파일 시스템(MVP) 또는 Secrets Manager(운영)에 저장한다.

프론트 연동 흐름:
  1) POST /platform-accounts/session → 세션 JSON 본문을 받아 저장
  2) GET  /platform-accounts → 연동된 계정 목록
  3) DELETE /platform-accounts/{id} → 연동 해제(세션 삭제)
"""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user_id
from app.domain.mapping.config import ACTIVE_PLATFORMS
from app.models.platform_account import PlatformAccount
from app.schemas.platform import PlatformAccountOut

router = APIRouter(prefix="/platform-accounts", tags=["platform-accounts"])

# MVP: 세션 파일 저장 경로. 운영에선 Secrets Manager 로 대체.
_SESSION_DIR = Path(__file__).resolve().parent.parent.parent.parent / "auth" / "users"


class PlatformSessionCreate(BaseModel):
    """프론트에서 전달하는 플랫폼 세션 데이터.

    session_data 는 Playwright storage_state 형식의 JSON(쿠키+로컬스토리지).
    프론트에서 팝업 로그인 후 쿠키를 수집해 보내주면 됨.
    """
    platform: str
    session_data: dict  # Playwright storage_state 호환 JSON


@router.get("", response_model=list[PlatformAccountOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """현재 사용자의 연동된 플랫폼 계정 목록."""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == user_id,
            PlatformAccount.is_active == True,
        )
    )
    return list(result.scalars().all())


@router.post("/session", response_model=PlatformAccountOut, status_code=201)
async def connect_platform(
    body: PlatformSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """플랫폼 로그인 세션을 저장해 계정을 연동한다.

    프론트에서 팝업으로 플랫폼에 로그인 → 쿠키/로컬스토리지를 수집 →
    이 API에 session_data 로 전달. 서버가 세션 파일로 저장하고 DB에 기록.
    """
    if body.platform not in ACTIVE_PLATFORMS:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 플랫폼: {body.platform}. 가능: {list(ACTIVE_PLATFORMS)}",
        )

    # 기존 연동이 있으면 갱신(덮어쓰기)
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == user_id,
            PlatformAccount.platform == body.platform,
        )
    )
    account = result.scalar_one_or_none()

    if account is None:
        account = PlatformAccount(
            user_id=user_id,
            platform=body.platform,
            credential_key="",  # 아래에서 파일 경로로 채움
            is_active=True,
        )
        db.add(account)
        await db.flush()  # id 확보

    # 세션 파일 저장
    user_dir = _SESSION_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    session_path = user_dir / f"{body.platform}.json"
    session_path.write_text(json.dumps(body.session_data, ensure_ascii=False), encoding="utf-8")

    account.credential_key = str(session_path)
    account.is_active = True
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=204)
async def disconnect_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """플랫폼 연동 해제. 세션 파일도 삭제."""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    # 세션 파일 삭제
    session_path = Path(account.credential_key)
    if session_path.exists():
        session_path.unlink()

    account.is_active = False
    await db.commit()
    return None
