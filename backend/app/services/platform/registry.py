from __future__ import annotations
"""[여원] platform 문자열 → 어댑터 매핑.

`get_adapter("karrot", browser)` 형태로 브라우저를 주입해 어댑터를 생성한다.
eBay 는 공식 API 기반이라 브라우저를 사용하지 않는다.
"""

from app.services.platform.base import PlatformAdapter
from app.services.platform.browser import BrowserAutomation
from app.services.platform.karrot import KarrotAdapter
from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.fruits import FruitsAdapter
from app.services.platform.charan import CharanAdapter
from app.services.platform.junggonara import JunggonaraAdapter
from app.services.platform.ebay import EbayAdapter

# 브라우저 자동화를 사용하는 어댑터.
_BROWSER_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "karrot": KarrotAdapter,
    "bunjang": BunjangAdapter,
    "fruits": FruitsAdapter,
    "charan": CharanAdapter,
    "junggonara": JunggonaraAdapter,
}

# 공식 API 기반(브라우저 불필요) 어댑터.
_API_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "ebay": EbayAdapter,
}


def get_adapter(platform: str, browser: BrowserAutomation | None = None) -> PlatformAdapter:
    """플랫폼 문자열로 어댑터 인스턴스를 반환한다.

    브라우저 자동화 어댑터는 browser 주입이 필요하다. 미지원 플랫폼은
    자격증명/시크릿을 노출하지 않는 에러를 던진다.
    """
    if platform in _BROWSER_ADAPTERS:
        if browser is None:
            raise ValueError(f"Platform '{platform}' requires a browser instance")
        return _BROWSER_ADAPTERS[platform](browser)
    if platform in _API_ADAPTERS:
        return _API_ADAPTERS[platform]()
    raise ValueError(f"Unknown platform: {platform}")
