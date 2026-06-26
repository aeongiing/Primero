"""[여원] 발행 오케스트레이션 테스트 (작업 7).

매핑→보류 판단→등록→결과 보고와, 부분 실패 격리를 검증한다.
실제 사이트/브라우저 없이 가짜 어댑터를 주입한다.
"""

import pytest

from app.domain.mapping import CanonicalProduct
from app.services.automation.publisher import (
    PublishStatus,
    publish_product,
)
from app.services.platform.base import ListingPayload, PlatformAdapter, PlatformError
from app.services.platform.browser import Credentials


class _FakeAdapter(PlatformAdapter):
    """등록 호출을 기록하는 가짜 어댑터. fail=True 면 등록 시 예외."""

    def __init__(self, platform: str, fake_id: str = "PID", fail: bool = False):
        self.platform = platform
        self._fake_id = fake_id
        self._fail = fail
        self.calls: list[ListingPayload] = []

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        self.calls.append(payload)
        if self._fail:
            raise PlatformError("등록 실패(테스트)")
        return self._fake_id

    async def is_sold(self, credentials, platform_product_id):  # noqa: D401
        return False

    async def delete_listing(self, credentials, platform_product_id):
        return None


def _product(**overrides) -> CanonicalProduct:
    base = dict(
        title="빈티지 자켓",
        brand="Levi's",
        description="설명",
        category="아우터",
        condition=8.0,
        price=45000,
        size="L",
    )
    base.update(overrides)
    return CanonicalProduct(**base)


def _creds(_platform: str) -> Credentials:
    return Credentials(username="u", password="p")


async def test_publishes_to_all_platforms_success():
    adapters = {
        "bunjang": _FakeAdapter("bunjang", "BJ-1"),
        "junggonara": _FakeAdapter("junggonara", "JG-1"),
    }
    outcomes = await publish_product(
        _product(), ["bunjang", "junggonara"],
        adapter_for=lambda p: adapters[p],
        credentials_for=_creds,
    )

    assert {o.platform: o.status for o in outcomes} == {
        "bunjang": PublishStatus.listed,
        "junggonara": PublishStatus.listed,
    }
    ids = {o.platform: o.platform_product_id for o in outcomes}
    assert ids == {"bunjang": "BJ-1", "junggonara": "JG-1"}


async def test_one_failure_does_not_block_others():
    adapters = {
        "bunjang": _FakeAdapter("bunjang", fail=True),       # 실패
        "junggonara": _FakeAdapter("junggonara", "JG-9"),    # 성공
    }
    outcomes = await publish_product(
        _product(), ["bunjang", "junggonara"],
        adapter_for=lambda p: adapters[p],
        credentials_for=_creds,
    )

    by_platform = {o.platform: o for o in outcomes}
    assert by_platform["bunjang"].status is PublishStatus.failed
    assert by_platform["bunjang"].error is not None
    # 한 곳 실패해도 다른 곳은 정상 등록
    assert by_platform["junggonara"].status is PublishStatus.listed
    assert by_platform["junggonara"].platform_product_id == "JG-9"


async def test_missing_required_is_held_not_called():
    # 제목이 비면 필수값 부족 → 보류(어댑터 호출 안 함)
    adapter = _FakeAdapter("bunjang")
    outcomes = await publish_product(
        _product(title=""), ["bunjang"],
        adapter_for=lambda p: adapter,
        credentials_for=_creds,
    )

    assert outcomes[0].status is PublishStatus.held
    assert "title" in outcomes[0].missing_required
    assert adapter.calls == []  # 등록 시도조차 하지 않는다


async def test_payload_carries_image_paths():
    adapter = _FakeAdapter("junggonara", "JG-2")
    await publish_product(
        _product(), ["junggonara"],
        adapter_for=lambda p: adapter,
        credentials_for=_creds,
        image_paths=("/tmp/1.jpg", "/tmp/2.jpg"),
    )
    assert adapter.calls[0].image_paths == ("/tmp/1.jpg", "/tmp/2.jpg")
    # 중고나라는 컨디션이 중고/새상품으로 매핑되어 전달된다
    assert adapter.calls[0].fields["condition"] == "중고"


async def test_empty_platforms_returns_empty():
    outcomes = await publish_product(
        _product(), [],
        adapter_for=lambda p: _FakeAdapter(p),
        credentials_for=_creds,
    )
    assert outcomes == []
