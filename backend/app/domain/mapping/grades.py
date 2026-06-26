"""[여원] 컨디션 점수 → 플랫폼 등급 변환 (순수).

steering(platform-upload.md) 매핑 규칙:
  9.0~10.0 = Excellent
  8.0~8.9  = Great
  6.5~7.9  = Very-good
  0.0~6.4  = Good
"""

# 경계값은 '이상' 기준 내림차순. (하한, 등급)
_GRADE_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (9.0, "Excellent"),
    (8.0, "Great"),
    (6.5, "Very-good"),
    (0.0, "Good"),
)


def condition_to_grade(score: float) -> str:
    """0~10 컨디션 점수를 차란 등급 문자열로 변환한다.

    범위를 벗어난 값은 가장 가까운 경계로 포화시킨다(>10 → Excellent, <0 → Good).
    """
    for lower, grade in _GRADE_THRESHOLDS:
        if score >= lower:
            return grade
    return "Good"
