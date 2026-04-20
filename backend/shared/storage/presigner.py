from __future__ import annotations

import boto3

from backend.shared.config import settings


def generate_presigned_url(object_key: str, expiry_seconds: int = 3600) -> str:
    client_kwargs = {
        "service_name": "s3",
        "region_name": settings.s3_region,
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": settings.s3_secret_access_key,
    }
    if settings.s3_endpoint_url:
        client_kwargs["endpoint_url"] = settings.s3_endpoint_url

    client = boto3.client(**client_kwargs)
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": object_key},
        ExpiresIn=expiry_seconds,
    )
