"""[여원] 플랫폼 매핑 엔진 예시 기반 테스트 (작업 7 - 도메인 코어)."""

import pytest

from app.domain.mapping import CanonicalProduct, condition_to_grade, map_product


def _product(**overrides) -> CanonicalProduct:
    base = dict(
        title="빈티지 데님 자켓",
        brand="Levi's",
        description="90년대 빈티지.",
        category="남성의류>아우터>재킷>데님재킷",
        condition=8.0,
        price=45000,
        size="L",
        colors=("블랙", "차콜"),
        materials=("면", "폴리에스터", "울", "나일론", "실크"),
        seasons=("봄", "가을", "겨울", "여름"),
    )
    base.update(overrides)
    return CanonicalProduct(**base)


@pytest.mark.parametrize(
    "score,grade",
    [
        (10.0, "Excellent"),
        (9.0, "Excellent"),
        (8.9, "Great"),
        (8.0, "Great"),
        (7.9, "Very-good"),
        (6.5, "Very-good"),
        (6.4, "Good"),
        (0.0, "Good"),
    ],
)
def test_condition_to_grade_boundaries(score: float, grade: str):
    assert condition_to_grade(score) == grade


def test_charan_full_mapping_ok():
    result = map_product(_product(), "charan")
    assert result.ok
    assert result.missing_required == []
    assert result.payload["condition"] == "Great"          # 8.0
    assert result.payload["colors"] == ["블랙"]              # 대표 색상 1개
    assert len(result.payload["materials"]) == 4            # 최대 4개 절단
    assert len(result.payload["seasons"]) == 4
    # 소재는 허용목록(우선순위) 순으로 정렬되어야 한다: 면<폴리에스터<울<나일론
    assert result.payload["materials"] == ["면", "폴리에스터", "울", "나일론"]


def test_charan_unmapped_color_collected():
    result = map_product(_product(colors=("형광초록",)), "charan")
    assert "colors" in result.unmapped_fields
    assert result.unmapped_fields["colors"] == ["형광초록"]
    # 대표 색상이 매핑 안 됨 → payload 에 colors 없음
    assert "colors" not in result.payload


def test_charan_missing_brand_is_required():
    result = map_product(_product(brand=""), "charan")
    assert not result.ok
    assert "brand" in result.missing_required


def test_charan_invalid_size_unmapped_and_missing():
    result = map_product(_product(size="XXL"), "charan")
    assert result.unmapped_fields.get("size") == ["XXL"]
    assert "size" in result.missing_required


def test_bunjang_folds_condition_into_description():
    result = map_product(_product(), "bunjang")
    assert result.ok
    # 번개는 등급 필드 없음
    assert "condition" not in result.payload
    assert "[컨디션] Great" in result.payload["description"]
    # 계절/소재 미지원 → payload 에 없음
    assert "seasons" not in result.payload
    assert "materials" not in result.payload


def test_karrot_size_is_free_string():
    result = map_product(_product(size="095 / L"), "karrot")
    assert result.ok
    assert result.payload["size"] == "095 / L"


def test_unknown_platform_raises():
    with pytest.raises(ValueError):
        map_product(_product(), "nonexistent")
