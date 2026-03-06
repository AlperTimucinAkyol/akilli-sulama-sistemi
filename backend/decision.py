import asyncio
from services.weather_service import WeatherService
class DecisionLogic:
    # ŞU AN İÇİN BURDAN ALIYORUZ FAKAT DAHA SONRA irrigation_rules GİBİ BİR TABLODAN ÇEKECEĞİZ
    MOISTURE_THRESHOLD = 40
    RAIN_THRESHOLD = 1  # mm
    
    @classmethod
    def decide_irrigation(cls, moisture_value: float, location: str):
        if moisture_value >= cls.MOISTURE_THRESHOLD:
            print("Toprak nemli. Sulama gerek yok.")
            return "OFF"

        forecast_summary = asyncio.run(WeatherService.get_irrigation_summary(location))
        print(forecast_summary)
        if forecast_summary is None:
            print("Hava tahmini alınamadı. Güvenlik nedeniyle sulama kapalı.")
            return "OFF"

        expected_rain_mm = forecast_summary["rain_3h"]
        if expected_rain_mm > cls.RAIN_THRESHOLD:
            print(f"Nem düşük ama {location} için yakında yağmur var. Sulama ertelendi.")
            return "OFF"
        else:
            print(f"Nem düşük ve {location} için yağmur yok. Sulama başlatılıyor.")
            return "ON"