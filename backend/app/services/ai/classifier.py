"""[윤채린] 의류 카테고리·색상 자동 분류.

AWS Rekognition(DetectLabels) + K-Fashion 모델을 사용해 카테고리와
대표 색상을 추출한다.
"""


async def classify(s3_keys: list[str]) -> dict:
    """대표 이미지 기준 카테고리·색상을 반환한다.

    Returns:
        {"category": str, "colors": list[str], "material": str | None}

    TODO:
      - Rekognition DetectLabels 호출 (S3 객체 직접 참조)
      - K-Fashion 모델로 세부 카테고리 보정
      - 색상 추출(Rekognition / Pillow 색 군집화)
    """
    raise NotImplementedError
