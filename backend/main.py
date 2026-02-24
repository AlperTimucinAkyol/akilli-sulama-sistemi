from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import Base, engine
from fastapi import FastAPI, HTTPException
from services.weather_service import WeatherService
from mqtt_client import start_mqtt_thread
from sqlalchemy import text
import models

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("DB bağlantısı başarılı:", result.scalar())
    except Exception as e:
        print("DB bağlantısı hatası:", e)
        
    print("MQTT başlatılıyor...")
    start_mqtt_thread()
    yield 

app = FastAPI(lifespan=lifespan)

@app.get("/")
def index():
    return {
        "status": "online",
        "message": "Akıllı Sulama Sistemi API Çalışıyor",
        "database": "connected"
    }

@app.get("/api/weather/irrigation-check")
async def check_irrigation_status():
    """
    Hava durumu verilerini çeker ve sulama karar mekanizması için 
    özetlenmiş veriyi döner.
    """
    summary = await WeatherService.get_irrigation_summary()

    if summary is None:
        raise HTTPException(
            status_code=503, 
            detail="Hava durumu servisine şu an ulaşılamıyor. Lütfen daha sonra tekrar deneyin."
        )

    return {
        "status": "success",
        "data": summary
    }

# karar mekanizmasını tetikleyen route
@app.get("/api/irrigation/decision")
async def get_irrigation_decision():
    summary = await WeatherService.get_irrigation_summary()
    
    if not summary:
        raise HTTPException(status_code=500, detail="Hava durumu verisi eksik.")

    # should_irrigate = decision_engine.calculate(summary)
    
    return {"decision": "Wait", "reason": "Rain expected soon"}