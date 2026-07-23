from fastapi import APIRouter

router = APIRouter()

@router.get("/health-check", tags=["Health"])
async def health_check() -> bool:
    return True