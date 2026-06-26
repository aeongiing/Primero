"""[여원] Fruits 어댑터 (Playwright 기반).

⚠️ 셀렉터/URL 은 실제 Fruits 웹 DOM 분석 후 채워야 한다.
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class FruitsAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="fruits",
        login=LoginSpec(
            url="",
            username_selector="",
            password_selector="",
            submit_selector="",
            success_selector="",
        ),
        new_listing_url="",
        fields=(
            FormField("title", ""),
            FormField("category", "", FieldKind.select),
            FormField("description", ""),
            FormField("price", ""),
        ),
        image_field=FormField("images", "", FieldKind.files),
        submit_selector="",
        listing_id_selector="",
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="sold",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
