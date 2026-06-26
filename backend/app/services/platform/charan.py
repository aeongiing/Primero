"""[여원] 차란 어댑터 (Playwright 기반).

⚠️ 셀렉터/URL 은 실제 차란 웹 DOM 분석 후 채워야 한다. 차란은 표현력이 가장 커
브랜드·사이즈(S/M/L)·컨디션 등급·색상·소재 등 추가 필드를 받는다.
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class CharanAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="charan",
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
            FormField("brand", ""),
            FormField("category", "", FieldKind.select),
            FormField("size", "", FieldKind.select),       # S/M/L
            FormField("condition", "", FieldKind.select),  # Excellent/Great/Very-good/Good
            FormField("description", ""),
            FormField("price", ""),
        ),
        image_field=FormField("images", "", FieldKind.files),
        submit_selector="",
        listing_id_selector="",
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="판매완료",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
