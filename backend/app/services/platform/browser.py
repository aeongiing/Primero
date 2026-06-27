from __future__ import annotations
"""[여원] 브라우저 자동화 포트 + Playwright 구현.

공식 API 가 없는 플랫폼(당근/번개/Fruits/차란)은 실제 브라우저를 자동 조작해
등록/조회/삭제한다. 어댑터는 이 추상 포트(BrowserAutomation/BrowserPage)에만
의존하므로, 테스트에서는 가짜 구현을 주입해 실제 사이트 접속 없이 검증한다.

Playwright 는 무거운 선택 의존이라 실제 구현 내부에서 지연 import 한다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Credentials:
    """플랫폼 로그인 자격증명(평문). Secrets Manager 에서 조회해 주입한다."""
    username: str
    password: str


class BrowserPage(ABC):
    """단일 페이지에 대한 최소 조작 인터페이스(포트)."""

    @abstractmethod
    async def goto(self, url: str) -> None: ...

    @abstractmethod
    async def fill(self, selector: str, value: str) -> None: ...

    @abstractmethod
    async def select_option(self, selector: str, value: str) -> None: ...

    @abstractmethod
    async def set_input_files(self, selector: str, files: list[str]) -> None: ...

    @abstractmethod
    async def click(self, selector: str) -> None: ...

    @abstractmethod
    async def text_content(self, selector: str) -> str | None: ...

    @abstractmethod
    async def get_attribute(self, selector: str, name: str) -> str | None: ...

    @abstractmethod
    async def current_url(self) -> str: ...

    @abstractmethod
    async def wait_for_timeout(self, ms: int) -> None: ...


class BrowserAutomation(ABC):
    """브라우저 세션 포트. 페이지를 만들고 정리한다."""

    @abstractmethod
    async def new_page(self) -> BrowserPage: ...

    @abstractmethod
    async def close(self) -> None: ...


# ---- Playwright 실제 구현 ---------------------------------------------------


class PlaywrightPage(BrowserPage):
    """Playwright Page 를 BrowserPage 포트로 감싼 어댑터."""

    def __init__(self, page):
        self._page = page

    async def goto(self, url: str) -> None:
        await self._page.goto(url, wait_until="networkidle")
        # 번개장터 앱 다운로드 팝업 제거
        try:
            await self._page.evaluate("document.querySelectorAll('.bun-ui-portal').forEach(el => el.remove())")
        except Exception:
            pass

    async def fill(self, selector: str, value: str) -> None:
        await self._page.fill(selector, value)

    async def select_option(self, selector: str, value: str) -> None:
        await self._page.select_option(selector, value)

    async def set_input_files(self, selector: str, files: list[str]) -> None:
        # 요소가 DOM에 나타날 때까지 대기 후 hidden 제거
        await self._page.wait_for_selector(selector, state="attached", timeout=30000)
        await self._page.evaluate(f"document.querySelector('{selector}').removeAttribute('hidden')")
        await self._page.set_input_files(selector, files)

    async def click(self, selector: str) -> None:
        await self._page.click(selector)

    async def text_content(self, selector: str) -> str | None:
        return await self._page.text_content(selector)

    async def get_attribute(self, selector: str, name: str) -> str | None:
        return await self._page.get_attribute(selector, name)

    async def current_url(self) -> str:
        return self._page.url

    async def wait_for_timeout(self, ms: int) -> None:
        await self._page.wait_for_timeout(ms)


class PlaywrightBrowser(BrowserAutomation):
    """Chromium 기반 실제 브라우저 자동화.

    실행 전 1회 `playwright install chromium` 이 필요하다. 헤드리스 여부는
    설정(browser_headless)에서 주입한다.

    storage_state(로그인 세션 파일)를 주면 이미 로그인된 상태로 시작한다.
    이 파일은 인증 토큰을 담으므로 비밀로 취급한다(auth/ gitignore).
    """

    def __init__(self, headless: bool = True, storage_state: str | None = None):
        self._headless = headless
        self._storage_state = storage_state
        self._pw = None
        self._browser = None

    async def _ensure_browser(self) -> None:
        if self._browser is None:
            from playwright.async_api import async_playwright  # 지연 import

            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=self._headless)

    async def new_page(self) -> BrowserPage:
        await self._ensure_browser()
        kwargs: dict = {}
        if self._storage_state and Path(self._storage_state).exists():
            kwargs["storage_state"] = self._storage_state
        context = await self._browser.new_context(**kwargs)
        page = await context.new_page()
        return PlaywrightPage(page)

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._pw is not None:
            await self._pw.stop()
            self._pw = None
