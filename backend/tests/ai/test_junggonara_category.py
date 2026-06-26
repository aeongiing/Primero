"""[여원] 중고나라 카테고리 매핑(성별 기반) 테스트.

AI 결과의 gender 로 중고나라 카테고리(패션의류 > 여성/남성의류)를 정한다.
"""

import pytest

from app.services.ai.pipeline import _map_junggonara


def _result(gender: str) -> dict:
    return {
        "title": "빈티지 자켓",
        "description": "설명",
        "materials": ["면"],
        "gender": gender,
    }


@pytest.mark.parametrize(
    "gender,expected",
    [
        ("남성", "패션의류 > 남성의류"),
        ("여성", "패션의류 > 여성의류"),
        ("공용", "패션의류 > 여성의류"),   # 공용 기본값
    ],
)
def test_junggonara_category_by_gender(gender: str, expected: str):
    mapping = _map_junggonara(_result(gender))
    assert mapping.platform == "junggonara"
    assert mapping.category == expected


def test_junggonara_unknown_gender_defaults_to_women():
    mapping = _map_junggonara({"title": "t", "description": "d", "gender": "??"})
    assert mapping.category == "패션의류 > 여성의류"


def test_junggonara_materials_appended_to_description():
    mapping = _map_junggonara(_result("남성"))
    assert "소재: 면" in mapping.description
