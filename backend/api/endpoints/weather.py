from fastapi import APIRouter, HTTPException
from services.weather_service import WeatherService

router = APIRouter()

@router.get("/current")
async def get_weather(location: str):
    weather_data = await WeatherService.fetch_weather_data(location)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="Hava durumu verisi alınamadı.")
    
    forecast_summary = weather_data.get_next_forecast() 
    
    return {
        "temp": forecast_summary["temp"],
        "condition": forecast_summary["condition"], 
        "pop": forecast_summary["pop"]
    }