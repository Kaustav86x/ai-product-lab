from fastapi import APIRouter, FastAPI

from app.routes import health  # importing the child router ( health.py) 
from app.routes.users import get_user  # importing the child router ( get_user.py)

internal_router = APIRouter()  # aggregate router to include all child routers
app = FastAPI()                # main FastAPI app, declared only once in the project

internal_router.include_router(health.router)  # including the child router ( health.py ) into the aggregate router
internal_router.include_router(get_user.router)  # including the child router ( get_user.py ) into the aggregate router
app.include_router(internal_router)            # including the aggregate router into the main FastAPI app