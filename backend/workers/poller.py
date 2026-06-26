"""[여원] 판매 완료 폴링 워커.

각 active 리스팅을 주기적으로 폴링해 판매 완료를 감지하면
sold_sync 를 트리거한다. ECS Fargate 상시 워커 또는 EventBridge +
Lambda 로 배포한다.
"""

import asyncio


async def poll_once() -> None:
    """active 리스팅을 1회 폴링한다.

    TODO:
      - active Listing 조회 → adapter.is_sold 확인
      - 판매 감지 시 automation.sold_sync.sync_sold 호출
    """
    raise NotImplementedError


async def run() -> None:
    """폴링 루프 (Fargate 상시 워커용)."""
    while True:
        await poll_once()
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run())
