"""[여원] 상품 등록 속성 기반 테스트 (작업 5).

Feature: parapara-upload-automation, Property 1
  유효한 ProductCreate 로 생성한 표준_상품은 GET 으로 조회 시 입력 필드가
  손실/변형 없이 그대로 round-trip 되어야 한다(SSOT 무결성).

각 속성 테스트는 최소 100회 반복한다(steering: tech.md).
"""

import asyncio
import uuid

from hypothesis import given, settings, strategies as st
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.deps import get_current_user_id
from app.main import app
from app.models.user import User

# 제어/서로게이트 문자를 제외한 안전한 텍스트(저장소 round-trip 안정성)
_safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
    min_size=1,
    max_size=50,
)

product_payloads = st.fixed_dictionaries(
    {
        "title": _safe_text,
        "brand": _safe_text,
        "description": _safe_text,
        "category": _safe_text,
        "condition": st.integers(min_value=1, max_value=10),
        "price": st.integers(min_value=1, max_value=100_000_000),
        "size": st.one_of(st.none(), st.text(max_size=20)),
        "colors": st.lists(_safe_text, max_size=5),
        "materials": st.lists(_safe_text, max_size=6),
        "platforms": st.lists(
            st.sampled_from(["karrot", "bunjang", "fruits", "charan"]),
            max_size=4,
        ),
    }
)


async def _round_trip(payload: dict) -> None:
    """격리된 인메모리 DB 에서 생성→조회를 수행하고 무결성을 검증한다."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with maker() as session:
            owner = User(email=f"{uuid.uuid4()}@e.com", google_id=str(uuid.uuid4()))
            session.add(owner)
            await session.commit()
            await session.refresh(owner)

            async def _db():
                yield session

            async def _uid():
                return owner.id

            app.dependency_overrides[get_db] = _db
            app.dependency_overrides[get_current_user_id] = _uid
            try:
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://t") as ac:
                    created = await ac.post("/api/v1/products", json=payload)
                    assert created.status_code == 201, created.text
                    cid = created.json()["id"]

                    fetched = await ac.get(f"/api/v1/products/{cid}")
                    assert fetched.status_code == 200
                    data = fetched.json()

                # 입력 필드가 그대로 보존되어야 한다
                for field in ("title", "brand", "description", "category", "condition", "price"):
                    assert data[field] == payload[field]
                assert data["size"] == payload["size"]
                assert data["colors"] == payload["colors"]
                assert data["materials"] == payload["materials"]
                # 신규 상품은 항상 draft, 소유자 일치
                assert data["status"] == "draft"
                assert data["user_id"] == str(owner.id)
            finally:
                app.dependency_overrides.clear()
    finally:
        await engine.dispose()


@settings(max_examples=100, deadline=None)
@given(payload=product_payloads)
def test_create_get_round_trip_preserves_fields(payload: dict):
    asyncio.run(_round_trip(payload))
