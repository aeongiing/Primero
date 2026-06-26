"""[윤채린] 썸네일 누끼 + 보정 처리.

rembg(U^2-Net)로 배경 제거 후 Pillow로 배경 합성·밝기/대비 보정·
정사각 썸네일 리사이즈를 수행한다. ECS Fargate AI 워커에서 실행.
"""


async def make_thumbnail(s3_key: str) -> str:
    """원본 이미지에서 누끼+보정된 썸네일을 생성해 S3 key 를 반환한다.

    TODO:
      - S3에서 원본 다운로드
      - rembg.remove() 로 배경 제거
      - Pillow: 흰 배경 합성 → ImageEnhance 밝기/대비 보정 → 정사각 리사이즈
      - 썸네일 S3 업로드 후 key 반환
    """
    raise NotImplementedError
