"""미디어 서비스 단위 테스트 — thumbnail."""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from PIL import Image

from app.services.media.thumbnail import _thumb_key, _process


class TestThumbKey:
    def test_normal_key(self):
        assert _thumb_key("user/prod/0.jpg") == "user/prod/0_thumb.jpg"

    def test_no_extension(self):
        assert _thumb_key("user/prod/0") == "user/prod/0_thumb"

    def test_png(self):
        assert _thumb_key("a/b/1.png") == "a/b/1_thumb.png"


class TestProcess:
    @patch("app.services.media.thumbnail.remove")
    def test_process_outputs_jpeg(self, mock_remove):
        # Create a dummy input image
        img = Image.new("RGB", (500, 500), (100, 150, 200))
        buf = BytesIO()
        img.save(buf, format="PNG")
        input_bytes = buf.getvalue()

        # Mock rembg to return RGBA image
        fg = Image.new("RGBA", (500, 500), (100, 150, 200, 255))
        fg_buf = BytesIO()
        fg.save(fg_buf, format="PNG")
        mock_remove.return_value = fg_buf.getvalue()

        result = _process(input_bytes)

        # Verify output is valid JPEG
        out_img = Image.open(BytesIO(result))
        assert out_img.format == "JPEG"
        assert out_img.size == (1000, 1000)


@pytest.mark.asyncio
class TestMakeThumbnail:
    @patch("app.services.media.thumbnail._download_and_upload")
    async def test_make_thumbnail_returns_key(self, mock_fn):
        from app.services.media.thumbnail import make_thumbnail

        mock_fn.return_value = "user/prod/0_thumb.jpg"
        result = await make_thumbnail("user/prod/0.jpg")
        assert result == "user/prod/0_thumb.jpg"
