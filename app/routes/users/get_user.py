from fastapi import APIRouter

router = APIRouter()

@router.get("/users/{user_name}", tags=["Users"])
async def get_user(user_name: str):
    return {"user_name": user_name}
