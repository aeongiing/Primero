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

import logging
import re

from app.services.platform.base import FormPlatformAdapter, BrowserPage, Credentials, ListingPayload, PlatformError
from app.services.platform.forms import (
    FieldKind, FormField, LoginSpec, PlatformFormSpec, PopupSelect,
)

logger = logging.getLogger(__name__)


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

    async def _screenshot(self, pw_page, name: str) -> None:
        try:
            import os
            os.makedirs("/tmp/bunjang_debug", exist_ok=True)
            path = f"/tmp/bunjang_debug/{name}.png"
            await pw_page.screenshot(path=path)
            logger.info(f"[bunjang] 스크린샷 저장: {path}")
        except Exception as e:
            logger.warning(f"[bunjang] 스크린샷 실패: {e}")

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        """번개장터 전용 등록 로직 — 카테고리/상품상태를 하드코딩 셀렉터로 처리."""
        logger.info(f"[bunjang] 등록 시작 — fields: {list(payload.fields.keys())}, images: {len(payload.image_paths)}장")
        page = await self.browser.new_page()
        await self._login(page, credentials)
        await page.goto(self.spec.new_listing_url)

        # Playwright 네이티브 page 접근 (카테고리 정확 매칭에 필요)
        pw_page = page._page

        current_url = await page.current_url()
        logger.info(f"[bunjang] goto 후 URL: {current_url}")
        await self._screenshot(pw_page, "01_after_goto")

        if "login" in current_url or "products/new" not in current_url:
            logger.error(f"[bunjang] 등록 페이지 진입 실패 — 세션 만료 의심. URL: {current_url}")
            raise PlatformError(f"번개장터 등록 페이지 진입 실패: {current_url}")

        logger.info("[bunjang] 등록 페이지 진입 성공")

        # 1) 사진 업로드 (실패해도 계속 진행)
        if self.spec.image_field and payload.image_paths:
            try:
                pw_input = await pw_page.query_selector(self.spec.image_field.selector)
                if pw_input:
                    await pw_page.evaluate("el => el.removeAttribute('hidden')", pw_input)
                    await pw_input.set_input_files(list(payload.image_paths))
                    logger.info(f"[bunjang] 이미지 업로드 완료: {len(payload.image_paths)}장")
                else:
                    logger.warning("[bunjang] #media-input 엘리먼트 없음")
            except Exception as e:
                logger.warning(f"[bunjang] 이미지 업로드 스킵: {e}")
        await self._screenshot(pw_page, "02_after_image")

        # 2) 상품명
        title = payload.fields.get("title", "")
        try:
            if title:
                await page.fill('input[name="common.name"]', title)
                logger.info(f"[bunjang] 상품명 입력 완료: {title[:20]}")
        except Exception as e:
            logger.warning(f"[bunjang] 상품명 입력 스킵: {e}")
        await self._screenshot(pw_page, "03_after_title")

        # 3) 카테고리 (실패해도 계속 진행)
        try:
            category = payload.fields.get("category", "")
            if category and ">" not in category:
                title_lower = title.lower()
                sub_map = {
                    "맨투맨": "맨투맨", "후드": "후드티/후드집업", "니트": "니트/스웨터",
                    "셔츠": "셔츠", "반팔": "반팔 티셔츠", "긴팔": "긴팔 티셔츠",
                    "패딩": "패딩", "코트": "코트", "자켓": "자켓",
                    "청바지": "데님/청바지", "슬랙스": "슬랙스",
                }
                detail = next((v for k, v in sub_map.items() if k in title_lower), "맨투맨")
                category = f"남성의류 > {category} > {detail}"
            logger.info(f"[bunjang] 카테고리 시도: {category}")
            if category:
                for seg in category.split(">"):
                    seg = seg.strip()
                    if seg:
                        el = await pw_page.query_selector(f'#scroll-categoryId span:text-is("{seg}")')
                        if el:
                            li = await el.evaluate_handle('e => e.closest("li")')
                            await li.as_element().click()
                            await pw_page.wait_for_timeout(800)
                            logger.info(f"[bunjang] 카테고리 클릭: {seg}")
                        else:
                            logger.warning(f"[bunjang] 카테고리 엘리먼트 없음: {seg}")
        except Exception as e:
            logger.warning(f"[bunjang] 카테고리 선택 스킵: {e}")
        await self._screenshot(pw_page, "04_after_category")

        # 4) 상품상태 (실패해도 계속 진행)
        try:
            condition = payload.fields.get("condition", "") or "사용감 없음"
            logger.info(f"[bunjang] 상품상태 시도: {condition}")
            await page.click('#scroll-condition button')
            await pw_page.wait_for_timeout(500)
            await pw_page.locator(f'li[role="option"]:has-text("{condition}")').click()
            logger.info(f"[bunjang] 상품상태 완료: {condition}")
        except Exception as e:
            logger.warning(f"[bunjang] 상품상태 선택 스킵: {e}")
        await self._screenshot(pw_page, "05_after_condition")

        # 4.5) 사이즈 선택 (실패해도 계속 진행)
        try:
            size = payload.fields.get("size", "L") or "L"
            logger.info(f"[bunjang] 사이즈 시도: {size}")
            await page.click('#scroll-option button[aria-haspopup="dialog"]')
            await pw_page.wait_for_timeout(1000)
            size_span = await pw_page.query_selector(f'span:text-is("{size}")')
            if size_span:
                size_li = await size_span.evaluate_handle('e => e.closest("li")')
                await size_li.as_element().click()
                await pw_page.wait_for_timeout(500)
                confirm = await pw_page.query_selector('button:has-text("완료"):not([disabled])')
                if confirm:
                    await confirm.click()
                    await pw_page.wait_for_timeout(500)
                logger.info(f"[bunjang] 사이즈 완료: {size}")
            else:
                logger.warning(f"[bunjang] 사이즈 엘리먼트 없음: {size}")
        except Exception as e:
            logger.warning(f"[bunjang] 사이즈 선택 스킵: {e}")
        await self._screenshot(pw_page, "06_after_size")

        # 5) 설명 (실패해도 계속 진행)
        try:
            desc = payload.fields.get("description", "")
            if desc:
                await pw_page.fill('textarea', desc)
                logger.info(f"[bunjang] 설명 입력 완료: {len(desc)}자")
        except Exception as e:
            logger.warning(f"[bunjang] 설명 입력 스킵: {e}")

        # 6) 가격 (필수 — 실패하면 경고만)
        try:
            price = payload.fields.get("price", "")
            if price:
                await page.fill('input[placeholder^="가격을 입력"]', str(price))
                logger.info(f"[bunjang] 가격 입력 완료: {price}")
        except Exception as e:
            logger.warning(f"[bunjang] 가격 입력 스킵: {e}")
        await self._screenshot(pw_page, "07_before_submit")

        # 7) 등록하기 클릭
        logger.info("[bunjang] 등록하기 클릭")
        await page.click('button[type="submit"]')

        # 등록 후 URL에서 상품 ID 추출 (리다이렉트 대기)
        await page.wait_for_timeout(5000)
        url = await page.current_url()
        logger.info(f"[bunjang] 등록 후 URL: {url}")
        await self._screenshot(pw_page, "08_after_submit")

        match = re.search(r'/products/(\d+)', url)
        if match:
            logger.info(f"[bunjang] 등록 성공 — 상품 ID: {match.group(1)}")
            return match.group(1)

        # URL에서 못 찾으면 data-pid 시도
        if self.spec.listing_id_attribute:
            listing_id = await page.get_attribute(
                self.spec.listing_id_selector, self.spec.listing_id_attribute
            )
            if listing_id:
                return listing_id

        raise PlatformError("bunjang: 등록 후 상품 ID를 찾지 못했습니다")
