import httpx
from config import WEATHER_API_KEY 
from schemas.weather_schemas import WeatherForecastResponse

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    @classmethod
    async def fetch_weather_data(cls):
        """
        OpenWeather API'den hava durumu verilerini çeker ve Pydantic modeline dönüştürür.
        """
        params = {
            "q": "Istanbul",
            "appid": WEATHER_API_KEY,
            "units": "metric", 
            "cnt": 8           # Önümüzdeki 24 saati verir
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(cls.BASE_URL, params=params)
                
                response.raise_for_status()
                
                raw_data = response.json()
                
                weather_model = WeatherForecastResponse(**raw_data)
                
                return weather_model

            except httpx.HTTPStatusError as e:
                print(f"API Hatası: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"Beklenmedik bir hata oluştu: {e}")
                return None

    @classmethod
    async def get_irrigation_summary(cls):
        """
        Karar mekanizması (decision.py) için sadeleştirilmiş veriyi döner.
        """
        data = await cls.fetch_weather_data()
        if data:
            return data.get_next_forecast()
        return None