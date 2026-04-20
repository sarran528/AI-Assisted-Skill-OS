from __future__ import annotations

import mimetypes
from uuid import UUID, uuid4

from backend.shared.config import settings
from backend.shared.errors import BusinessError
from backend.shared.storage.presigner import generate_presigned_url
from backend.shared.storage.s3_client import get_s3_client

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "video/mp4",
}
MAX_FILE_BYTES = 52_428_800


def detect_mime_type(file_bytes: bytes, original_filename: str) -> str:
    try:
        import magic  # type: ignore

        return str(magic.from_buffer(file_bytes, mime=True))
    except Exception:
        guessed, _ = mimetypes.guess_type(original_filename)
        return guessed or "application/octet-stream"


async def upload_evidence_file(
    file_bytes: bytes,
    original_filename: str,
    session_id: UUID,
    checkpoint_id: str,
    user_id: UUID,
) -> tuple[str, str, str]:
    if len(file_bytes) > MAX_FILE_BYTES:
        raise BusinessError("file_too_large", "Evidence file exceeds 50MB limit")

    mime_type = detect_mime_type(file_bytes, original_filename)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise BusinessError("unsupported_mime_type", f"MIME type '{mime_type}' is not allowed")

    object_key = (
        f"evidence/{user_id}/{session_id}/{checkpoint_id}/{uuid4()}/{original_filename}"
    )

    async with get_s3_client() as s3_client:
        await s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            Body=file_bytes,
            ContentType=mime_type,
        )

    artifact_url = generate_presigned_url(object_key, expiry_seconds=3600)
    return object_key, artifact_url, mime_type
