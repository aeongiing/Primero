"""[여원] 상품 소유권 격리 테스트 (작업 5).

표준_상품은 항상 소유자 범위로만 접근 가능해야 한다. 다른 사용자의 상품은
조회/수정/삭제 시 404 로 막힌다(부분 실패 격리 및 SSOT 접근통제).
"""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductStatus
from app.models.user import User


async def _make_product(db: AsyncSession, owner_id) -> Product:
    p = Product(
        user_id=owner_id,
        title="남의 상품",
        brand="BrandX",
        description="다른 사용자 소유 상품",
        category="여성의류>상의>티셔츠",
        condition=7,
        price=12000,
        status=ProductStatus.draft,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def test_cannot_get_other_users_product(
    client: AsyncClient, db_session: AsyncSession, other_user: User
):
    foreign = await _make_product(db_session, other_user.id)
    resp = await client.get(f"/api/v1/products/{foreign.id}")
    assert resp.status_code == 404


async def test_cannot_update_other_users_product(
    client: AsyncClient, db_session: AsyncSession, other_user: User
):
    foreign = await _make_product(db_session, other_user.id)
    resp = await client.patch(f"/api/v1/products/{foreign.id}", json={"price": 1})
    assert resp.status_code == 404


async def test_cannot_delete_other_users_product(
    client: AsyncClient, db_session: AsyncSession, other_user: User
):
    foreign = await _make_product(db_session, other_user.id)
    resp = await client.delete(f"/api/v1/products/{foreign.id}")
    assert resp.status_code == 404


async def test_list_excludes_other_users_products(
    client: AsyncClient, db_session: AsyncSession, other_user: User
):
    await _make_product(db_session, other_user.id)
    resp = await client.get("/api/v1/products")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_listings_of_other_users_product_is_404(
    client: AsyncClient, db_session: AsyncSession, other_user: User
):
    foreign = await _make_product(db_session, other_user.id)
    resp = await client.get(f"/api/v1/listings/{foreign.id}")
    assert resp.status_code == 404
