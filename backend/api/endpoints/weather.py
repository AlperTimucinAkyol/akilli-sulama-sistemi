from fastapi import APIRouter, HTTPException
from services.weather_service import WeatherService

router = APIRouter()

@router.get("/irrigation-check")
async def check_irrigation_status():
    summary = await WeatherService.get_irrigation_summary("Trabzon")
    if summary is None:
        raise HTTPException(status_code=503, detail="Hava durumu servisine ulaşılamıyor.")
    return {"status": "success", "data": summary}