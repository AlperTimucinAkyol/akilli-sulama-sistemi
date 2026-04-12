from fastapi import APIRouter
from api.endpoints import weather, auth, fields, users, irrigation

api_router = APIRouter()

# prefix="/weather" diyerek tüm hava durumu endpoint'lerini grupluyoruz
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(fields.router, prefix="/fields", tags=["Fields"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(irrigation.router, prefix="/irrigation", tags=["Irrigation"])