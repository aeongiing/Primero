from __future__ import annotations
"""[윤채린] 의류 분류 + 설명 생성 (Claude 멀티모달 통합).

Anthropic API를 직접 호출해 카테고리·색상·소재·패턴·계절·스타일·제목·브랜드·설명을
한 번에 추출한다.
"""

import asyncio
import base64
import json
from functools import lru_cache
from typing import Dict, List, Tuple

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
  "brand": "브랜드명 (태그/로고에서 확인 가능할 때만. 불확실하면 빈 문자열 \\"\\")",
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


def _build_content_from_payloads(payloads: List[Tuple[bytes, str]]) -> list:
    """(이미지 바이트, media_type) 목록 → Claude content 블록."""
    content = []
    for data, media in payloads[:6]:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media or "image/jpeg",
                "data": base64.b64encode(data).decode(),
            },
        })
    content.append({"type": "text", "text": "이 의류를 분석해주세요."})
    return content


def _build_content(s3_keys: List[str]) -> list:
    """S3 key 목록 → 바이트 로드 → content 블록."""
    return _build_content_from_payloads(
        [(_get_image_bytes(key), "image/jpeg") for key in s3_keys[:6]]
    )


def _invoke_content(content: list) -> Dict:
    import anthropic

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        base_url=settings.anthropic_base_url or None,
    )

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=800,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    text = message.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def _invoke(s3_keys: List[str]) -> Dict:
    return _invoke_content(_build_content(s3_keys))


def _invoke_bytes(payloads: List[Tuple[bytes, str]]) -> Dict:
    return _invoke_content(_build_content_from_payloads(payloads))


async def analyze_with_claude(s3_keys: List[str]) -> Dict:
    """S3 이미지를 Claude에 전송해 분류+설명을 반환한다."""
    return await asyncio.to_thread(_invoke, s3_keys)


async def analyze_with_claude_bytes(payloads: List[Tuple[bytes, str]]) -> Dict:
    """업로드된 이미지 바이트를 (S3 없이) 바로 Claude에 전송해 분석한다."""
    return await asyncio.to_thread(_invoke_bytes, payloads)


# ─── 핏 추천 (텍스트 전용) ───

_FIT_SYSTEM_PROMPT_FEMALE = """\
당신은 의류 핏 분석 전문가입니다.
주어진 카테고리·표기 사이즈·실측(cm)을 바탕으로, 이 옷이
- 어떤 키/몸무게/체형에게 '정핏'으로 맞는지
- 어떤 키/몸무게/체형에게 '오버핏'으로 맞는지
를 한국어로 추천하세요.

규칙:
- 체형은 '스트레이트 / 웨이브 / 내추럴' 중에서 사용합니다.
- 실측값이 없으면 표기 사이즈로 일반적인 범위를 추정하되 단정하지 말고 '대략'으로 표현합니다.
- 키는 범위(예: 160~165cm), 몸무게도 범위로 제시합니다.
- 과장·확신 없이 2~4문장으로 자연스럽게. 마크다운/JSON 없이 본문 텍스트만 출력하세요."""

_FIT_SYSTEM_PROMPT_DEFAULT = """\
당신은 의류 핏 분석 전문가입니다.
주어진 카테고리·표기 사이즈·실측(cm)을 바탕으로, 이 옷이
- 어떤 키/몸무게에게 '정핏'으로 맞는지
- 어떤 키/몸무게에게 '오버핏'으로 맞는지
를 한국어로 추천하세요.

규칙:
- 실측값이 없으면 표기 사이즈로 일반적인 범위를 추정하되 단정하지 말고 '대략'으로 표현합니다.
- 키는 범위(예: 170~175cm), 몸무게도 범위로 제시합니다.
- 과장·확신 없이 2~4문장으로 자연스럽게. 마크다운/JSON 없이 본문 텍스트만 출력하세요."""


def _invoke_fit_text(user_text: str, gender: str | None) -> str:
    import anthropic

    system = _FIT_SYSTEM_PROMPT_FEMALE if gender == "여성의류" else _FIT_SYSTEM_PROMPT_DEFAULT

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        base_url=settings.anthropic_base_url or None,
    )
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )
    return message.content[0].text.strip()


async def recommend_fit(info: dict) -> str:
    """카테고리·사이즈·실측 → 정핏/오버핏 추천 텍스트."""
    lines = [
        f"카테고리: {info.get('category') or '-'}",
        f"표기 사이즈: {info.get('size') or '-'}",
    ]
    measures = []
    for key, label in [
        ("chest", "가슴단면"),
        ("shoulder", "어깨너비"),
        ("sleeve", "소매길이"),
        ("total_length", "총장"),
    ]:
        val = info.get(key)
        if val:
            measures.append(f"{label} {val}cm")
    lines.append("실측: " + (", ".join(measures) if measures else "없음(표기 사이즈로 추정)"))
    user_text = "\n".join(lines) + "\n\n이 옷의 정핏/오버핏 추천을 작성해줘."
    return await asyncio.to_thread(_invoke_fit_text, user_text, info.get("gender"))
