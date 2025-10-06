from fastapi import APIRouter

router = APIRouter()


@router.get("/example", tags=["example"])
def example_endpoint():
    """Simple example endpoint to show routing under /api"""
    return {"message": "This is an example endpoint under /api/example"}
