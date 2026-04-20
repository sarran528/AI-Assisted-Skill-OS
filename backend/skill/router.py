from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_skills() -> dict:
	return {"items": []}
