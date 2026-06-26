"""[여원] 상품 CRUD API 통합 테스트 (작업 5).

표준_상품(SSOT) 의 생성/조회/수정/삭제와 소유권 격리를 검증한다.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User


def _valid_payload(**overrides) -> dict:
    body = {
        "title": "빈티지 데님 자켓",
        "brand": "Levi's",
        "description": "90년대 빈티지 데님 자켓입니다.",
        "category": "남성의류>아우터>재킷>데님재킷",
        "condition": 8,
        "price": 45000,
        "size": "L",
        "colors": ["블랙", "차콜"],
        "materials": ["면", "폴리에스터"],
        "platforms": ["bunjang", "junggonara"],
    }
    body.update(overrides)
    return body


async def test_create_product_persists_and_returns_draft(client: AsyncClient, user: User):
    resp = await client.post("/api/v1/products", json=_valid_payload())
    assert resp.status_code == 201

    data = resp.json()
    assert data["title"] == "빈티지 데님 자켓"
    assert data["price"] == 45000
    assert data["status"] == "draft"
    assert data["user_id"] == str(user.id)
    assert data["images"] == []
    assert data["colors"] == ["블랙", "차콜"]
    assert data["materials"] == ["면", "폴리에스터"]
    # 생성 응답은 유효한 UUID 를 가진다
    uuid.UUID(data["id"])


async def test_create_then_get_round_trip(client: AsyncClient):
    created = (await client.post("/api/v1/products", json=_valid_payload())).json()

    resp = await client.get(f"/api/v1/products/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["brand"] == "Levi's"


async def test_list_products_filters_by_status(client: AsyncClient):
    await client.post("/api/v1/products", json=_valid_payload(title="A"))
    await client.post("/api/v1/products", json=_valid_payload(title="B"))

    all_resp = await client.get("/api/v1/products")
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 2

    # 생성 직후 상태는 draft → listed 필터는 비어 있어야 한다
    listed = await client.get("/api/v1/products", params={"status": "listed"})
    assert listed.json() == []

    draft = await client.get("/api/v1/products", params={"status": "draft"})
    assert len(draft.json()) == 2


async def test_update_product_changes_fields(client: AsyncClient):
    created = (await client.post("/api/v1/products", json=_valid_payload())).json()

    resp = await client.patch(
        f"/api/v1/products/{created['id']}",
        json={"price": 39000, "description": "가격 인하했습니다."},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == 39000
    assert resp.json()["description"] == "가격 인하했습니다."
    # 수정하지 않은 필드는 유지된다
    assert resp.json()["title"] == "빈티지 데님 자켓"


async def test_delete_product_removes_it(client: AsyncClient):
    created = (await client.post("/api/v1/products", json=_valid_payload())).json()

    resp = await client.delete(f"/api/v1/products/{created['id']}")
    assert resp.status_code == 204

    missing = await client.get(f"/api/v1/products/{created['id']}")
    assert missing.status_code == 404


async def test_get_missing_product_returns_404(client: AsyncClient):
    resp = await client.get(f"/api/v1/products/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.parametrize("bad", [{"condition": 0}, {"condition": 11}, {"price": 0}, {"price": -1}])
async def test_create_rejects_invalid_values(client: AsyncClient, bad: dict):
    resp = await client.post("/api/v1/products", json=_valid_payload(**bad))
    assert resp.status_code == 422


async def test_colors_materials_default_to_empty_lists(client: AsyncClient):
    payload = _valid_payload()
    del payload["colors"]
    del payload["materials"]

    resp = await client.post("/api/v1/products", json=payload)
    assert resp.status_code == 201
    assert resp.json()["colors"] == []
    assert resp.json()["materials"] == []


@pytest.mark.parametrize("platforms", [["karrot"], ["charan", "bunjang"], ["fruits"], ["ebay"]])
async def test_create_rejects_inactive_platforms(client: AsyncClient, platforms: list):
    resp = await client.post("/api/v1/products", json=_valid_payload(platforms=platforms))
    assert resp.status_code == 422


async def test_create_accepts_active_platforms(client: AsyncClient):
    resp = await client.post("/api/v1/products", json=_valid_payload(platforms=["bunjang", "junggonara"]))
    assert resp.status_code == 201
