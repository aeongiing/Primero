"""[여원] 테스트용 가짜 브라우저.

실제 사이트 접속 없이 어댑터 로직(폼 입력 순서/값/제출/ID 추출)을 검증한다.
모든 동작을 records 에 기록한다.
"""

from app.services.platform.browser import BrowserAutomation, BrowserPage


class FakePage(BrowserPage):
    def __init__(self, texts: dict[str, str] | None = None, attrs: dict[tuple[str, str], str] | None = None):
        self.records: list[tuple] = []
        self._texts = texts or {}
        self._attrs = attrs or {}
        self._url = ""

    async def goto(self, url: str) -> None:
        self._url = url
        self.records.append(("goto", url))

    async def fill(self, selector: str, value: str) -> None:
        self.records.append(("fill", selector, value))

    async def select_option(self, selector: str, value: str) -> None:
        self.records.append(("select", selector, value))

    async def set_input_files(self, selector: str, files: list[str]) -> None:
        self.records.append(("files", selector, tuple(files)))

    async def click(self, selector: str) -> None:
        self.records.append(("click", selector))

    async def text_content(self, selector: str) -> str | None:
        self.records.append(("text", selector))
        return self._texts.get(selector)

    async def get_attribute(self, selector: str, name: str) -> str | None:
        self.records.append(("attr", selector, name))
        return self._attrs.get((selector, name))

    async def current_url(self) -> str:
        return self._url


class FakeBrowser(BrowserAutomation):
    def __init__(self, page: FakePage | None = None):
        self.page = page or FakePage()
        self.closed = False

    async def new_page(self) -> BrowserPage:
        return self.page

    async def close(self) -> None:
        self.closed = True
