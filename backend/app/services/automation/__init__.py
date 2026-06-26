"""[여원] 자동화 서비스.

플랫폼 발행·동기화·할인 등 비즈니스 자동화 로직.
"""

from app.services.automation.auto_discount import apply_weekly_discount
from app.services.automation.delete_service import delete_all_listings
from app.services.automation.listing_service import publish_to_platforms
from app.services.automation.publisher import publish_product, publish_to_platform
from app.services.automation.sold_sync import sync_sold
from app.services.automation.update_service import update_listing_price

__all__ = [
    "apply_weekly_discount",
    "delete_all_listings",
    "publish_to_platforms",
    "publish_product",
    "publish_to_platform",
    "sync_sold",
    "update_listing_price",
]
