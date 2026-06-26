"""[여원] 플랫폼 어댑터 인터페이스 + 폼 기반 공통 구현.

각 플랫폼은 등록/조회/삭제 3개 동작을 표준화한 PlatformAdapter 를 구현한다.
공식 API 가 없는 플랫폼은 FormPlatformAdapter 를 상속해 선언적 폼 스펙만
제공하면 된다(브라우저 조작 로직은 공통).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.services.platform.browser import BrowserAutomation, BrowserPage, Credentials
from app.services.platform.forms import FieldKind, PlatformFormSpec


@dataclass
class ListingPayload:
    """플랫폼에 등록할 상품 데이터.

    - fields: 플랫폼_매핑_엔진이 생성한 payload(title/price/category/description/…).
    - image_paths: 업로드할 로컬 이미지 파일 경로(S3 키에서 내려받아 준비된 상태).
    """
    fields: dict
    image_paths: tuple[str, ...] = ()


class PlatformError(Exception):
    """플랫폼 자동화 실패. 메시지에 자격증명/시크릿을 포함하지 않는다."""


class PlatformAdapter(ABC):
    """플랫폼별 등록/동기화 어댑터."""

    platform: str

    @abstractmethod
    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        """등록 후 플랫폼 측 상품 ID 반환."""
        ...

    @abstractmethod
    async def is_sold(self, credentials: Credentials, platform_product_id: str) -> bool:
        """판매 완료 여부 폴링."""
        ...

    @abstractmethod
    async def delete_listing(self, credentials: Credentials, platform_product_id: str) -> None:
        """플랫폼에서 상품 삭제."""
        ...


class FormPlatformAdapter(PlatformAdapter):
    """선언적 폼 스펙을 브라우저로 실행하는 공통 어댑터.

    브라우저 포트(BrowserAutomation)에만 의존하므로 테스트에서 가짜 브라우저를
    주입할 수 있다.
    """

    spec: PlatformFormSpec

    def __init__(self, browser: BrowserAutomation):
        self.browser = browser
        self.platform = self.spec.platform

    async def _login(self, page: BrowserPage, credentials: Credentials) -> None:
        login = self.spec.login
        # 로그인 URL 이 없으면 저장된 세션(storage_state) 기반으로 간주하고 폼 로그인 생략.
        if not login.url:
            return
        await page.goto(login.url)
        await page.fill(login.username_selector, credentials.username)
        await page.fill(login.password_selector, credentials.password)
        await page.click(login.submit_selector)

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        page = await self.browser.new_page()
        await self._login(page, credentials)
        await page.goto(self.spec.new_listing_url)

        for f in self.spec.fields:
            value = payload.fields.get(f.key)
            if value is None or value == "":
                continue
            if f.kind is FieldKind.select:
                await page.select_option(f.selector, str(value))
            elif f.kind is FieldKind.radio:
                target = f.options.get(str(value))
                if target:
                    await page.click(target)
            else:
                await page.fill(f.selector, str(value))

        if self.spec.image_field is not None and payload.image_paths:
            await page.set_input_files(self.spec.image_field.selector, list(payload.image_paths))

        await page.click(self.spec.submit_selector)

        if self.spec.listing_id_attribute:
            listing_id = await page.get_attribute(
                self.spec.listing_id_selector, self.spec.listing_id_attribute
            )
        else:
            listing_id = await page.text_content(self.spec.listing_id_selector)

        if not listing_id:
            raise PlatformError(f"{self.platform}: 등록 후 상품 ID 를 찾지 못했습니다")
        return listing_id

    async def is_sold(self, credentials: Credentials, platform_product_id: str) -> bool:
        page = await self.browser.new_page()
        await self._login(page, credentials)
        await page.goto(self.spec.listing_url_template.format(id=platform_product_id))
        text = await page.text_content(self.spec.sold_selector)
        return bool(text) and self.spec.sold_marker in text

    async def delete_listing(self, credentials: Credentials, platform_product_id: str) -> None:
        page = await self.browser.new_page()
        await self._login(page, credentials)
        await page.goto(self.spec.manage_url_template.format(id=platform_product_id))
        await page.click(self.spec.delete_selector)
        await page.click(self.spec.delete_confirm_selector)
