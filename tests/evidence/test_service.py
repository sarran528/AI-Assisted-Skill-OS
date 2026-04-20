from io import BytesIO
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from starlette.datastructures import UploadFile

from backend.evidence.service import upload_evidence


@pytest.mark.asyncio
async def test_upload_evidence_creates_record_with_validated_false():
    db = AsyncMock()
    user_id = uuid4()
    session_id = uuid4()

    fake_record = AsyncMock()
    fake_record.id = uuid4()
    fake_record.checkpoint_id = "cp1"
    fake_record.artifact_url = "https://example.com/artifact"
    fake_record.mime_type = "image/png"
    fake_record.file_size_bytes = 8
    fake_record.validated = False

    upload_file = UploadFile(filename="sample.png", file=BytesIO(b"pngbytes"))

    with patch("backend.evidence.service.upload_evidence_file", new=AsyncMock(return_value=("obj", "https://example.com/artifact", "image/png"))), patch(
        "backend.evidence.service.EvidenceRepository.create", new=AsyncMock(return_value=fake_record)
    ):
        record = await upload_evidence(
            db,
            upload_file,
            session_id,
            "cp1",
            user_id,
            "artifact",
        )

    assert record.validated is False
    assert record.checkpoint_id == "cp1"
