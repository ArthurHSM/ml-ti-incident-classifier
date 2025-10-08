from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", tags=["health"])
def get_health():
	"""Health-check moved from app.py into api router."""
	return {"status": "ok", "service": "ml-ti-incident-classifier"}
