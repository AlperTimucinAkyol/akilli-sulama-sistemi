import asyncio
from sqlalchemy.orm import Session
from models.iot import IrrigationRule
from services.weather_service import WeatherService

 # Fallback (Varsayılan) Ayarlar
DEFAULT_RULE = {
    "min_soil_moisture": 25.0,
    "max_temperature": 38.0,
    "rain_block": True
}

class DecisionLogic:
    
    @classmethod
    async def decide_irrigation(cls, db: Session, field_id: int, current_moisture: float, current_temp: float, location: str):
        """
        Tarlaya özel kurala göre sulama kararı verir. 
        Kural yoksa varsayılan ayarları (Default Rule) kullanır.
        """
        rule = db.query(IrrigationRule).filter(IrrigationRule.field_id == field_id).first()
        
        if not rule:
            print(f"Tarla {field_id} için özel kural yok. Varsayılan ayarlar kullanılıyor.")
            # rule objesi yerine sözlük kullanacağımız için kontrollü erişim sağlıyoruz
            min_moisture = DEFAULT_RULE["min_soil_moisture"]
            max_temp = DEFAULT_RULE["max_temperature"]
            rain_block = DEFAULT_RULE["rain_block"]
        else:
            print(f"Tarla {field_id} için '{rule.name}' kuralı işleniyor.")
            min_moisture = rule.min_soil_moisture
            max_temp = rule.max_temperature
            rain_block = rule.rain_block

        # 2. KRİTİK KONTROL: Toprak Nemi
        if current_moisture >= min_moisture:
            print(f"Nem yeterli (%{current_moisture} >= %{min_moisture}). Sulama kapalı.")
            return "OFF"

        # 3. GÜVENLİK KONTROLÜ: Hava Sıcaklığı
        if current_temp >= max_temp:
            print(f"Hava çok sıcak ({current_temp}°C). Bitki sağlığı için sulama ertelendi.")
            return "OFF"

        # 4. AKILLI KONTROL: Hava Durumu (Yağmur Engeli)
        if rain_block:
            forecast_summary = await WeatherService.get_irrigation_summary(location)
            print(forecast_summary.get("rain_3h", 0))
            if forecast_summary and forecast_summary.get("rain_3h", 0) > 1.0:
                print(f"Nem düşük ama {location} için yakında yağmur bekleniyor. Su tasarrufu sağlandı.")
                return "OFF"

        # 5. KARAR: Tüm engeller aşıldıysa sulamayı başlat
        print(f"Koşullar uygun: Nem düşük, sıcaklık normal ve yağmur yok. Sulama başlatılıyor.")
        return "ON"