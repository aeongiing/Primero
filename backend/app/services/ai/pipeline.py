"""[윤채린] AI 분석 파이프라인 오케스트레이션.

S3 업로드된 이미지를 받아 분류(classifier) → 설명 생성(description)을
순서대로 호출하고 AIAnalysisResult로 합쳐 반환한다.
"""

from app.schemas.ai import AIAnalysisResult


async def analyze(s3_keys: list[str]) -> AIAnalysisResult:
    """이미지 S3 key 목록을 받아 종합 분석 결과를 반환한다.

    TODO:
      1. classifier.classify() 로 카테고리·색상 추출
      2. description.generate() 로 상품 설명 생성
      3. 결과를 AIAnalysisResult 로 병합
    """
    raise NotImplementedError
