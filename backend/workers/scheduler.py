"""[여원] 주기 작업 진입점.

EventBridge 스케줄(예: 매일 1회)이 호출하는 핸들러. 미판매 1주 상품
자동 할인 등을 실행한다.
"""

import asyncio
import logging

from app.services.automation.auto_discount import apply_weekly_discount

logger = logging.getLogger(__name__)


async def run() -> None:
    """주기 작업 1회 실행."""
    logger.info("Starting scheduled task: weekly discount")
    try:
        count = await apply_weekly_discount()
        logger.info(f"Scheduled task completed: {count} products discounted")
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}", exc_info=True)
        raise


def handler(event, context):
    """AWS Lambda 진입점 (EventBridge 스케줄 트리거)."""
    return asyncio.run(run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
