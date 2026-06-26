"""AI 서비스 단위 테스트 — classifier, description, pipeline."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.ai.classifier import classify, _closest_color, _extract_category, _extract_colors


class TestClosestColor:
    def test_black(self):
        assert _closest_color(0, 0, 0) == "블랙"

    def test_white(self):
        assert _closest_color(255, 255, 255) == "화이트"

    def test_red(self):
        assert _closest_color(200, 30, 30) == "레드"

    def test_navy(self):
        assert _closest_color(20, 25, 80) == "네이비"


class TestExtractCategory:
    def test_jacket(self):
        labels = [{"Name": "Jacket", "Confidence": 95}]
        assert _extract_category(labels) == "아우터 > 재킷"

    def test_dress(self):
        labels = [{"Name": "Dress", "Confidence": 90}]
        assert _extract_category(labels) == "원피스 > 원피스"

    def test_fallback(self):
        labels = [{"Name": "Person", "Confidence": 99}]
        assert _extract_category(labels) == "상의 > 티셔츠"


class TestExtractColors:
    def test_with_dominant_colors(self):
        response = {
            "ImageProperties": {
                "DominantColors": [
                    {"Red": 0, "Green": 0, "Blue": 0},
                    {"Red": 255, "Green": 255, "Blue": 255},
                ]
            }
        }
        colors = _extract_colors(response)
        assert "블랙" in colors
        assert "화이트" in colors

    def test_empty_fallback(self):
        assert _extract_colors({}) == ["블랙"]


@pytest.mark.asyncio
class TestClassify:
    @patch("app.services.ai.classifier._detect")
    async def test_classify_returns_expected_keys(self, mock_detect):
        mock_detect.return_value = {
            "Labels": [
                {"Name": "Coat", "Confidence": 95},
                {"Name": "Clothing", "Confidence": 99},
            ],
            "ImageProperties": {
                "DominantColors": [{"Red": 50, "Green": 50, "Blue": 50}]
            },
        }
        result = await classify(["test/key.jpg"])
        assert "category" in result
        assert "colors" in result
        assert result["category"] == "아우터 > 코트"


@pytest.mark.asyncio
class TestGenerate:
    @patch("app.services.ai.description._client")
    async def test_generate_returns_title_brand_desc(self, mock_client_fn):
        from app.services.ai.description import generate

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        body_content = b'{"content": [{"text": "{\\"title\\": \\"\\ud14c\\uc2a4\\ud2b8 \\uc0c1\\ud488\\", \\"brand\\": \\"\\ubbf8\\uc0c1\\", \\"description\\": \\"\\uc88b\\uc740 \\uc0c1\\ud488\\uc785\\ub2c8\\ub2e4\\"}"}]}'
        mock_body = MagicMock()
        mock_body.read.return_value = body_content
        mock_client.invoke_model.return_value = {"body": mock_body}

        result = await generate({"category": "상의", "colors": ["블랙"], "material": None, "pattern": "무지"})
        assert result["title"] == "테스트 상품"
        assert result["brand"] == "미상"


@pytest.mark.asyncio
class TestPipeline:
    @patch("app.services.ai.pipeline.generate")
    @patch("app.services.ai.pipeline.classify")
    async def test_analyze_returns_ai_result(self, mock_classify, mock_generate):
        from app.services.ai.pipeline import analyze

        mock_classify.return_value = {
            "category": "상의 > 니트",
            "colors": ["블랙"],
            "material": "울",
            "pattern": "무지",
        }
        mock_generate.return_value = {
            "title": "울 니트",
            "brand": "미상",
            "description": "깔끔한 울 니트입니다",
        }

        result = await analyze(["img.jpg"])
        assert result.title == "울 니트"
        assert result.category == "상의 > 니트"
        assert result.colors == ["블랙"]
        assert result.material == "울"
