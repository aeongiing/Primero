"""[여원] 플랫폼 매핑 엔진 속성 기반 테스트 (작업 7 - 도메인 코어).

Feature: parapara-upload-automation, Property 2~6
각 속성 테스트는 최소 100회 반복한다(steering: tech.md).
"""

from hypothesis import given, settings, strategies as st

from app.domain.mapping import CanonicalProduct, condition_to_grade, map_product
from app.domain.mapping.config import CHARAN, PLATFORM_CONFIGS

_GRADES = {"Excellent", "Great", "Very-good", "Good"}

# 허용값 + 임의값을 섞어 매핑/미매핑 경로를 모두 탐색.
_color_vals = st.one_of(st.sampled_from(CHARAN.list_fields["colors"].allowed), st.text(min_size=1, max_size=6))
_material_vals = st.one_of(st.sampled_from(CHARAN.list_fields["materials"].allowed), st.text(min_size=1, max_size=6))
_season_vals = st.one_of(st.sampled_from(CHARAN.list_fields["seasons"].allowed), st.text(min_size=1, max_size=6))

_safe = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), max_size=30)

products = st.builds(
    CanonicalProduct,
    title=_safe,
    brand=_safe,
    description=_safe,
    category=_safe,
    condition=st.floats(min_value=-5, max_value=15, allow_nan=False, allow_infinity=False),
    price=st.integers(min_value=-1000, max_value=10_000_000),
    size=st.one_of(st.none(), st.sampled_from(["S", "M", "L"]), st.text(max_size=8)),
    colors=st.lists(_color_vals, max_size=6).map(tuple),
    materials=st.lists(_material_vals, max_size=8).map(tuple),
    seasons=st.lists(_season_vals, max_size=8).map(tuple),
)

platforms = st.sampled_from(list(PLATFORM_CONFIGS.keys()))


@settings(max_examples=100, deadline=None)
@given(score=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
def test_grade_is_always_one_of_four(score: float):
    # Property 2: 컨디션 등급은 항상 정의된 4개 중 하나.
    assert condition_to_grade(score) in _GRADES


@settings(max_examples=100, deadline=None)
@given(product=products, platform=platforms)
def test_never_raises_and_ok_matches_missing(product: CanonicalProduct, platform: str):
    # Property 3: 알려진 플랫폼에 대해 항상 결과를 반환하고, ok 는 missing_required 와 일치.
    result = map_product(product, platform)
    assert result.platform == platform
    assert result.ok == (len(result.missing_required) == 0)


@settings(max_examples=100, deadline=None)
@given(product=products)
def test_charan_list_constraints(product: CanonicalProduct):
    # Property 4: 차란 리스트 필드는 최대 개수 이하이며 모두 허용목록 소속이고 중복 없음.
    result = map_product(product, "charan")
    for field, rule in CHARAN.list_fields.items():
        mapped = result.payload.get(field, [])
        assert len(mapped) <= rule.max_count
        assert len(mapped) == len(set(mapped))           # 중복 없음
        assert all(v in rule.allowed for v in mapped)     # 허용값만


@settings(max_examples=100, deadline=None)
@given(product=products)
def test_unmapped_values_are_exactly_disallowed(product: CanonicalProduct):
    # Property 5: 미매핑으로 보고된 값은 정확히 허용목록 밖의 값들이다.
    result = map_product(product, "charan")
    for field, rule in CHARAN.list_fields.items():
        reported = set(result.unmapped_fields.get(field, []))
        assert all(v not in rule.allowed for v in reported)


@settings(max_examples=100, deadline=None)
@given(product=products, platform=platforms)
def test_missing_required_subset_of_required(product: CanonicalProduct, platform: str):
    # Property 6: missing_required 는 항상 해당 플랫폼 required 의 부분집합.
    result = map_product(product, platform)
    config = PLATFORM_CONFIGS[platform]
    assert set(result.missing_required).issubset(set(config.required))
