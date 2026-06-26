"""[여원] 상품 → 다중 플랫폼 등록 태스크 발행.

상품 생성 시 선택된 플랫폼별로 SQS 메시지를 발행한다. 실제 등록은
워커(Lambda/Fargate)가 메시지를 소비해 platform 어댑터로 수행한다.
"""

import uuid


async def publish_listing_tasks(product_id: uuid.UUID, platforms: list[str]) -> None:
    """선택된 플랫폼별 등록 태스크를 SQS 로 발행한다.

    TODO:
      - boto3 SQS send_message_batch
      - 메시지 본문: {product_id, platform}
    """
    raise NotImplementedError
