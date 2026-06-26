"""[여원] platform 문자열 → 어댑터 매핑.

`get_adapter("karrot")` 형태로 어댑터 인스턴스를 조회한다.
"""

from app.services.platform.base import PlatformAdapter
from app.services.platform.karrot import KarrotAdapter
from app.services.platform.bunjang import BunjangAdapter
from app.services.platform.fruits import FruitsAdapter
from app.services.platform.charan import CharanAdapter
from app.services.platform.ebay import EbayAdapter

_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "karrot": KarrotAdapter,
    "bunjang": BunjangAdapter,
    "fruits": FruitsAdapter,
    "charan": CharanAdapter,
    "ebay": EbayAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    """플랫폼 문자열로 어댑터 인스턴스를 반환한다."""
    try:
        return _ADAPTERS[platform]()
    except KeyError:
        raise ValueError(f"Unknown platform: {platform}")
