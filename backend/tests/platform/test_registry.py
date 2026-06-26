"""[여원] 어댑터 레지스트리 테스트 (작업 7)."""

import pytest

from app.services.platform.base import FormPlatformAdapter, PlatformAdapter
from app.services.platform.ebay import EbayAdapter
from app.services.platform.registry import get_adapter
from tests.platform.fakes import FakeBrowser


@pytest.mark.parametrize("platform", ["karrot", "bunjang", "fruits", "charan", "junggonara"])
def test_browser_adapters_require_browser(platform: str):
    adapter = get_adapter(platform, FakeBrowser())
    assert isinstance(adapter, FormPlatformAdapter)
    assert adapter.platform == platform


@pytest.mark.parametrize("platform", ["karrot", "bunjang", "fruits", "charan", "junggonara"])
def test_browser_adapters_without_browser_raise(platform: str):
    with pytest.raises(ValueError):
        get_adapter(platform)


def test_ebay_is_api_adapter_no_browser_needed():
    adapter = get_adapter("ebay")
    assert isinstance(adapter, EbayAdapter)
    assert isinstance(adapter, PlatformAdapter)


def test_unknown_platform_raises():
    with pytest.raises(ValueError):
        get_adapter("amazon", FakeBrowser())
