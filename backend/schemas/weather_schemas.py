from pydantic import BaseModel, Field
from typing import List, Optional

class MainData(BaseModel):
    temp: float
    humidity: int

class WeatherDescription(BaseModel):
    main: str
    description: str

class ForecastItem(BaseModel):
    dt: int  # Zaman
    main: MainData
    weather: List[WeatherDescription]
    pop: float  # (Yağış Olasılığı 0-1 arası)
    
    rain: Optional[dict] = None 

class WeatherForecastResponse(BaseModel):
    list: List[ForecastItem]
    
    def get_next_forecast(self):
        """Listenin en başındaki (en yakın) tahmini döner."""
        next_data = self.list[0]
        return {
            "temp": next_data.main.temp,
            "humidity": next_data.main.humidity,
            "condition": next_data.weather[0].main,
            "pop": next_data.pop,
            "rain_3h": next_data.rain.get("3h", 0) if next_data.rain else 0
        }