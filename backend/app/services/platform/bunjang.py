"""[여원] 번개장터 어댑터 (Playwright 기반).

실제 등록 페이지(https://m.bunjang.co.kr/products/new) DOM 캡처로 확정한 셀렉터.

확정:
  - 상품명: input[name="common.name"]
  - 설명:   textarea[placeholder^="브랜드, 모델명"]
  - 가격:   input[placeholder^="가격을 입력"]
  - 사진:   #media-input (type=file)
  - 등록:   button[type="submit"] ("등록하기")
  - 카테고리: #scroll-categoryId 안의 li를 순서대로 클릭 (텍스트 정확 매칭)
  - 상품상태: #scroll-condition button → role=option li 텍스트 매칭
"""

from app.services.platform.base import FormPlatformAdapter, BrowserPage, Credentials, ListingPayload, PlatformError
from app.services.platform.forms import (
    FieldKind, FormField, LoginSpec, PlatformFormSpec, PopupSelect,
)


class BunjangAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="bunjang",
        login=LoginSpec(
            url="https://m.bunjang.co.kr/login",
            username_selector='input[placeholder*="전화번호"]',
            password_selector='input[placeholder*="인증번호"]',
            submit_selector='button[class*="_submitBtn_"]',
            success_selector='a[href="/my"]',
        ),
        new_listing_url="https://m.bunjang.co.kr/products/new",
        fields=(
            FormField("title", 'input[name="common.name"]'),
            FormField("description", 'textarea[placeholder^="브랜드, 모델명"]'),
            FormField("price", 'input[placeholder^="가격을 입력"]'),
        ),
        image_field=FormField("images", "#media-input", FieldKind.files),
        submit_selector='button[type="submit"]',
        category_container="#scroll-categoryId",
        popup_selects=(),
        listing_id_selector='[data-pid]',
        listing_id_attribute="data-pid",
        listing_url_template="https://m.bunjang.co.kr/products/{id}",
        sold_selector='div[class*="_statusBadge_"], span[class*="_saleBadge_"]',
        sold_marker="판매완료",
        manage_url_template="https://m.bunjang.co.kr/products/{id}/edit",
        delete_selector='button:has-text("삭제")',
        delete_confirm_selector='button[class*="_confirmBtn_"]:has-text("확인")',
        price_selector='input[placeholder^="가격을 입력"]',
        save_selector='button[type="submit"]:has-text("수정")',
    )

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        """번개장터 전용 등록 로직 — 카테고리/상품상태를 하드코딩 셀렉터로 처리."""
        page = await self.browser.new_page()
        await self._login(page, credentials)
        await page.goto(self.spec.new_listing_url)

        # Playwright 네이티브 page 접근 (카테고리 정확 매칭에 필요)
        pw_page = page._page

        # 1) 사진 업로드
        if self.spec.image_field and payload.image_paths:
            await page.set_input_files(self.spec.image_field.selector, list(payload.image_paths))

        # 2) 상품명
        title = payload.fields.get("title", "")
        if title:
            await page.fill('input[name="common.name"]', title)

        # 3) 카테고리 — span:text-is 정확 매칭 → 부모 li 클릭
        category = payload.fields.get("category", "")
        # 프론트에서 1단계만 오면 기본 경로로 보완
        if category and ">" not in category:
            title_lower = title.lower()
            gender = "남성의류"  # 기본값
            sub = category  # "상의", "아우터", "하의" 등
            # 타이틀에서 하위 카테고리 추론
            sub_map = {
                "맨투맨": "맨투맨", "후드": "후드티/후드집업", "니트": "니트/스웨터",
                "셔츠": "셔츠", "반팔": "반팔 티셔츠", "긴팔": "긴팔 티셔츠",
                "패딩": "패딩", "코트": "코트", "자켓": "자켓",
                "청바지": "데님/청바지", "슬랙스": "슬랙스",
            }
            detail = ""
            for keyword, bunjang_name in sub_map.items():
                if keyword in title_lower:
                    detail = bunjang_name
                    break
            if not detail:
                detail = "맨투맨"  # 기본 폴백
            category = f"{gender} > {sub} > {detail}"
        if category:
            for seg in category.split(">"):
                seg = seg.strip()
                if seg:
                    el = await pw_page.query_selector(f'#scroll-categoryId span:text-is("{seg}")')
                    if el:
                        li = await el.evaluate_handle('e => e.closest("li")')
                        await li.as_element().click()
                        await pw_page.wait_for_timeout(800)

        # 4) 상품상태 — 드롭다운 열고 옵션 선택
        condition = payload.fields.get("condition", "")
        if not condition:
            condition = "사용감 없음"  # 기본값
        await page.click('#scroll-condition button')
        await page.wait_for_timeout(500)
        await pw_page.locator(f'li[role="option"]:has-text("{condition}")').click()

        # 4.5) 사이즈 선택 (필수)
        size = payload.fields.get("size", "L") or "L"
        try:
            await page.click('#scroll-option button[aria-haspopup="dialog"]')
            await page.wait_for_timeout(1000)
            size_span = await pw_page.query_selector(f'span:text-is("{size}")')
            if size_span:
                size_li = await size_span.evaluate_handle('e => e.closest("li")')
                await size_li.as_element().click()
                await pw_page.wait_for_timeout(500)
                confirm = await pw_page.query_selector('button:has-text("완료"):not([disabled])')
                if confirm:
                    await confirm.click()
                    await pw_page.wait_for_timeout(500)
        except Exception:
            pass  # 사이즈 선택 실패해도 계속 진행

        # 5) 설명
        desc = payload.fields.get("description", "")
        if desc:
            await pw_page.fill('textarea', desc)

        # 6) 가격
        price = payload.fields.get("price", "")
        if price:
            await page.fill('input[placeholder^="가격을 입력"]', str(price))

        # 7) 등록하기 클릭
        await page.click('button[type="submit"]')

        # 등록 후 URL에서 상품 ID 추출 (리다이렉트 대기)
        await page.wait_for_timeout(5000)
        url = await page.current_url()
        # https://m.bunjang.co.kr/products/123456789
        import re
        match = re.search(r'/products/(\d+)', url)
        if match:
            return match.group(1)

        # URL에서 못 찾으면 data-pid 시도
        if self.spec.listing_id_attribute:
            listing_id = await page.get_attribute(
                self.spec.listing_id_selector, self.spec.listing_id_attribute
            )
            if listing_id:
                return listing_id

        raise PlatformError("bunjang: 등록 후 상품 ID를 찾지 못했습니다")
