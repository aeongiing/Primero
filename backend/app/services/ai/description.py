"""[윤채린] 상품 설명 자동 생성.

AWS Bedrock(Claude)를 사용해 분류 결과·치수·상태를 바탕으로
판매용 상품 제목과 설명을 생성한다.
"""


async def generate(attrs: dict) -> dict:
    """분류 속성을 받아 제목/브랜드/설명을 생성한다.

    Args:
        attrs: {"category", "colors", "material", "condition", ...}

    Returns:
        {"title": str, "brand": str, "description": str}

    TODO:
      - Bedrock Claude 프롬프트 구성
      - 응답 파싱 → 제목/설명 분리
    """
    raise NotImplementedError
