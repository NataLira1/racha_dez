from fastapi import APIRouter

from app.api.routes import arena, user, login, reservation

api_router = APIRouter()

api_router.include_router(arena.router)
api_router.include_router(user.router)
api_router.include_router(login.router)
api_router.include_router(reservation.router)
