"""[여원] 미판매 자동 할인.

등록 후 1주일간 미판매 상품의 가격을 10% 인하하고 연동된 모든
플랫폼에 변경을 반영한다. EventBridge 스케줄로 주기 실행.
"""


async def apply_weekly_discount() -> int:
    """1주 이상 미판매 상품에 10% 할인을 적용한다.

    Returns:
        할인이 적용된 상품 수.

    TODO:
      - listed_at 이 7일 이전이고 status=listed 인 상품 조회
      - price = round(price * 0.9)
      - 각 active 리스팅에 adapter 로 가격 갱신 반영
    """
    raise NotImplementedError
