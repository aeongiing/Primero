"""[여원] OpenClaw 클라이언트 래퍼.

OpenClaw 자동화 엔진을 통해 플랫폼 UI 동작을 수행하는 공통 HTTP 클라이언트.
각 플랫폼 어댑터가 이 클라이언트를 통해 실제 등록/삭제를 호출한다.
"""

import httpx

from app.core.config import settings


class OpenClawClient:
    """OpenClaw API 호출 래퍼."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.openclaw_api_url

    async def run(self, platform: str, action: str, credential_key: str, params: dict) -> dict:
        """OpenClaw 자동화 작업 실행.

        TODO:
          - Secrets Manager 에서 credential_key 로 자격증명 조회
          - OpenClaw 작업 요청 → 결과 반환
        """
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            raise NotImplementedError
