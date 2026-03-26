from fastapi import APIRouter
from api.endpoints import weather

api_router = APIRouter()

# prefix="/weather" diyerek tüm hava durumu endpoint'lerini grupluyoruz
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"]) # DÜZELTİLECEK
# api_router.include_router(irrigation.router, prefix="/irrigation", tags=["Irrigation"])