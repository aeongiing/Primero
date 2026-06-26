"""[여원] 테스트 공통 픽스처.

인메모리 SQLite(aiosqlite)로 격리된 DB 를 만들고, FastAPI 의존성(get_db,
get_current_user_id)을 오버라이드해 외부(AWS/Postgres) 없이 라우트를 검증한다.
"""

import os

# 앱 모듈 import 전에 DB URL 을 SQLite 로 강제해 asyncpg(Postgres) 의존을 피한다.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import uuid
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.deps import get_current_user_id
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def db_session():
    """테스트마다 새 인메모리 DB 와 스키마를 생성한다."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    """테스트용 소유자 1명을 만든다."""
    u = User(email="owner@example.com", google_id="google-owner")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    """소유권 격리 검증용 다른 사용자."""
    u = User(email="other@example.com", google_id="google-other")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, user: User):
    """get_db 와 현재 사용자(user)를 오버라이드한 테스트 클라이언트."""
    async def _override_db():
        yield db_session

    async def _override_user() -> uuid.UUID:
        return user.id

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user_id] = _override_user

    # 발행(Playwright 브라우저)을 모킹해 테스트에서 실제 사이트 접속 안 함.
    with patch(
        "app.services.automation.listing_service.publish_to_platforms",
        new_callable=AsyncMock,
        return_value=[],
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
