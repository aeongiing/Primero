"""[윤채린] 의류 분류 + 설명 생성 (Claude 멀티모달 통합).

Anthropic API를 직접 호출해 카테고리·색상·소재·패턴·계절·스타일·제목·브랜드·설명을
한 번에 추출한다.
"""

import asyncio
import base64
import json
from functools import lru_cache
from typing import Dict, List

import boto3

from app.core.config import settings


@lru_cache(maxsize=1)
def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def _get_image_bytes(s3_key: str) -> bytes:
    resp = _s3_client().get_object(Bucket=settings.s3_bucket, Key=s3_key)
    return resp["Body"].read()


_SYSTEM_PROMPT = """\
당신은 한국 중고 의류 판매 전문가이자 패션 분류 AI입니다.
업로드된 의류 이미지를 분석해 아래 JSON 형식으로만 응답하세요. 추가 텍스트 없이 JSON만 출력합니다.

{
  "title": "상품 제목 (30자 이내, 브랜드+아이템+특징)",
  "brand": "브랜드명 (태그에서 확인 불가하면 \\"미상\\")",
  "description": "상세 설명 (200자 내외, 소재감·핏·상태·코디 제안 포함)",
  "category": "카테고리 (아래 목록에서 선택)",
  "gender": "성별 (남성/여성/공용 중 하나)",
  "colors": ["대표 색상 (아래 목록에서 최대 2개)"],
  "materials": ["소재 (아래 목록에서 최대 4개)"],
  "pattern": "패턴 (아래 목록에서 1개)",
  "season": ["계절 (아래 목록에서 최대 4개)"],
  "style": ["스타일 (아래 목록에서 최대 2개)"]
}

카테고리 목록:
아우터 > 재킷, 아우터 > 점퍼, 아우터 > 조끼, 아우터 > 집업, 아우터 > 코트, 아우터 > 카디건,
상의 > 니트, 상의 > 티셔츠, 상의 > 블라우스/셔츠,
하의 > 팬츠, 하의 > 스커트,
원피스 > 원피스, 세트 > 정장세트, 세트 > 트레이닝 세트

성별 목록: 남성, 여성, 공용

색상 목록: 블랙, 차콜, 레드, 화이트, 그레이, 네이비, 아이보리, 베이지, 카키, 민트, 그린, 블루, 스카이 블루, 퍼플, 라벤더, 와인, 핑크, 옐로우, 오렌지, 브라운

소재 목록: 면, 폴리에스터, 폴리우레탄, 스판덱스, 데님, 리넨, 울, 천연가죽, 인조가죽, 천연퍼, 인조퍼, 캐시미어, 앙고라, 알파카, 코듀로이, 나일론, 실크, 레이온, 모달, 기모, 모헤어, 엘라스틴, 아크릴, 덕다운, 구스다운, 스웨이드

패턴 목록: 무지, 그래픽, 레터링, 스트라이프, 체크, 도트, 플라워, 페이즐리, 지브라, 레오파드, 타이다이

계절 목록: 봄, 여름, 가을, 겨울

스타일 목록: 스포티, 스트릿, 베이직, 러블리, 오피스, 캠퍼스, 청순, 섹시"""


def _build_content(s3_keys: List[str]) -> list:
    content = []
    for key in s3_keys[:4]:
        img_bytes = _get_image_bytes(key)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.b64encode(img_bytes).decode(),
            },
        })
    content.append({"type": "text", "text": "이 의류를 분석해주세요."})
    return content


def _invoke(s3_keys: List[str]) -> Dict:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=800,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_content(s3_keys)}],
    )

    text = message.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


async def analyze_with_claude(s3_keys: List[str]) -> Dict:
    """이미지를 Claude에 전송해 분류+설명을 한 번에 반환한다."""
    return await asyncio.to_thread(_invoke, s3_keys)
