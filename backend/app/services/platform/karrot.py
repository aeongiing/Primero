"""[여원] 당근마켓 어댑터 (Playwright 기반).

⚠️ 셀렉터/URL 은 실제 당근 웹 DOM 분석 후 채워야 한다. 현재는 폼 구조만 선언한
placeholder 다. (당근 카테고리: 여성의류/남성패션·잡화, 사이즈는 자유 문자열)
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class KarrotAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="karrot",
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
            FormField("size", ""),          # 자유 문자열
            FormField("description", ""),
            FormField("price", ""),
        ),
        image_field=FormField("images", "", FieldKind.files),
        submit_selector="",
        listing_id_selector="",
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="거래완료",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
