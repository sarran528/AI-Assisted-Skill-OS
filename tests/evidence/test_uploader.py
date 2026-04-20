from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.shared.errors import BusinessError
from backend.shared.storage.uploader import upload_evidence_file


@pytest.mark.asyncio
async def test_valid_png_upload_succeeds():
    with patch("backend.shared.storage.uploader.detect_mime_type", return_value="image/png"), patch(
        "backend.shared.storage.uploader.get_s3_client"
    ) as mock_client_factory, patch(
        "backend.shared.storage.uploader.generate_presigned_url",
        return_value="https://example.com/file",
    ):
        mock_client = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_client
        mock_client_factory.return_value = mock_context

        key, url, mime = await upload_evidence_file(
            b"png-bytes",
            "sample.png",
            uuid4(),
            "cp1",
            uuid4(),
        )

        assert "cp1" in key
        assert url == "https://example.com/file"
        assert mime == "image/png"


@pytest.mark.asyncio
async def test_txt_renamed_jpg_detected_as_text_plain():
    with patch("backend.shared.storage.uploader.detect_mime_type", return_value="text/plain"), patch(
        "backend.shared.storage.uploader.get_s3_client"
    ) as mock_client_factory, patch(
        "backend.shared.storage.uploader.generate_presigned_url",
        return_value="https://example.com/file",
    ):
        mock_client = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_client
        mock_client_factory.return_value = mock_context

        _, _, mime = await upload_evidence_file(
            b"not-an-image",
            "fake.jpg",
            uuid4(),
            "cp2",
            uuid4(),
        )
        assert mime == "text/plain"


@pytest.mark.asyncio
async def test_unsupported_mime_type_raises():
    with patch("backend.shared.storage.uploader.detect_mime_type", return_value="application/x-executable"):
        with pytest.raises(BusinessError) as exc:
            await upload_evidence_file(b"binary", "a.exe", uuid4(), "cp", uuid4())
        assert exc.value.code == "unsupported_mime_type"


@pytest.mark.asyncio
async def test_file_too_large_raises():
    with patch("backend.shared.storage.uploader.detect_mime_type", return_value="image/png"):
        with pytest.raises(BusinessError) as exc:
            await upload_evidence_file(b"a" * (52_428_800 + 1), "big.png", uuid4(), "cp", uuid4())
        assert exc.value.code == "file_too_large"
