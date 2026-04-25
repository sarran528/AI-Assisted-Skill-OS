from datetime import datetime
from uuid import UUID

from backend.shared.models import APIModel


class UserResponse(APIModel):
    id: UUID
    email: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        **APIModel.model_config,
        "from_attributes": True,
    }
