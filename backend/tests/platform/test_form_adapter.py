"""[여원] 폼 기반 어댑터 공통 로직 테스트 (작업 7 - Playwright 자동화).

가짜 브라우저로 로그인→필드입력→이미지업로드→제출→ID추출 흐름을 검증한다.
실제 플랫폼 셀렉터와 무관하게 동작이 정의대로인지 확인한다.
"""

import pytest

from app.services.platform.base import FormPlatformAdapter, ListingPayload, PlatformError
from app.services.platform.browser import Credentials
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec
from tests.platform.fakes import FakeBrowser, FakePage

_SPEC = PlatformFormSpec(
    platform="test",
    login=LoginSpec(
        url="https://t/login",
        username_selector="#user",
        password_selector="#pass",
        submit_selector="#login-btn",
        success_selector="#home",
    ),
    new_listing_url="https://t/new",
    fields=(
        FormField("title", "#title"),
        FormField("category", "#cat", FieldKind.select),
        FormField("description", "#desc"),
        FormField("price", "#price"),
    ),
    image_field=FormField("images", "#img", FieldKind.files),
    submit_selector="#submit",
    listing_id_selector="#result-id",
    listing_id_attribute=None,
    listing_url_template="https://t/item/{id}",
    sold_selector="#status",
    sold_marker="판매완료",
    manage_url_template="https://t/manage/{id}",
    delete_selector="#delete",
    delete_confirm_selector="#confirm",
)


class _TestAdapter(FormPlatformAdapter):
    spec = _SPEC


def _creds() -> Credentials:
    return Credentials(username="seller", password="secret")


def _payload(**fields) -> ListingPayload:
    base = {"title": "자켓", "category": "아우터", "description": "설명", "price": 45000}
    base.update(fields)
    return ListingPayload(fields=base, image_paths=("/tmp/a.jpg", "/tmp/b.jpg"))


async def test_create_listing_fills_and_returns_id():
    page = FakePage(texts={"#result-id": "ITEM-123"})
    adapter = _TestAdapter(FakeBrowser(page))

    listing_id = await adapter.create_listing(_creds(), _payload())

    assert listing_id == "ITEM-123"
    # 로그인 → 등록폼 이동 순서
    assert ("goto", "https://t/login") in page.records
    assert ("fill", "#user", "seller") in page.records
    assert ("goto", "https://t/new") in page.records
    # 필드 입력(텍스트/셀렉트 구분)
    assert ("fill", "#title", "자켓") in page.records
    assert ("select", "#cat", "아우터") in page.records
    assert ("fill", "#price", "45000") in page.records
    # 이미지 업로드 + 제출
    assert ("files", "#img", ("/tmp/a.jpg", "/tmp/b.jpg")) in page.records
    assert ("click", "#submit") in page.records


async def test_create_listing_skips_empty_fields():
    page = FakePage(texts={"#result-id": "X"})
    adapter = _TestAdapter(FakeBrowser(page))

    await adapter.create_listing(_creds(), _payload(description=""))

    fills = [r for r in page.records if r[0] == "fill" and r[1] == "#desc"]
    assert fills == []  # 빈 값은 입력하지 않는다


async def test_create_listing_without_id_raises():
    page = FakePage(texts={})  # result-id 없음
    adapter = _TestAdapter(FakeBrowser(page))

    with pytest.raises(PlatformError):
        await adapter.create_listing(_creds(), _payload())


async def test_create_listing_id_via_attribute():
    spec_attr = PlatformFormSpec(
        **{**_SPEC.__dict__, "listing_id_attribute": "data-id"}
    )

    class _AttrAdapter(FormPlatformAdapter):
        spec = spec_attr

    page = FakePage(attrs={("#result-id", "data-id"): "ATTR-9"})
    adapter = _AttrAdapter(FakeBrowser(page))

    assert await adapter.create_listing(_creds(), _payload()) == "ATTR-9"


@pytest.mark.parametrize(
    "status_text,expected",
    [("판매완료된 상품입니다", True), ("판매중", False), (None, False)],
)
async def test_is_sold(status_text, expected):
    texts = {"#status": status_text} if status_text is not None else {}
    page = FakePage(texts=texts)
    adapter = _TestAdapter(FakeBrowser(page))

    assert await adapter.is_sold(_creds(), "ITEM-1") is expected
    assert ("goto", "https://t/item/ITEM-1") in page.records


async def test_delete_listing_clicks_confirm():
    page = FakePage()
    adapter = _TestAdapter(FakeBrowser(page))

    await adapter.delete_listing(_creds(), "ITEM-7")

    assert ("goto", "https://t/manage/ITEM-7") in page.records
    assert ("click", "#delete") in page.records
    assert ("click", "#confirm") in page.records


async def test_radio_field_clicks_mapped_selector():
    radio_spec = PlatformFormSpec(
        **{
            **_SPEC.__dict__,
            "fields": (
                FormField("title", "#title"),
                FormField(
                    "condition", "", FieldKind.radio,
                    options={"중고": "#used", "새상품": "#new"},
                ),
            ),
        }
    )

    class _RadioAdapter(FormPlatformAdapter):
        spec = radio_spec

    page = FakePage(texts={"#result-id": "X"})
    adapter = _RadioAdapter(FakeBrowser(page))

    # condition=새상품 → #new 클릭
    payload = ListingPayload(fields={"title": "자켓", "condition": "새상품"})
    await adapter.create_listing(_creds(), payload)
    assert ("click", "#new") in page.records
    assert ("click", "#used") not in page.records
