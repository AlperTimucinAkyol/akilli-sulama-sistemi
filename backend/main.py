from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse          
from fastapi.staticfiles import StaticFiles         
from fastapi.templating import Jinja2Templates       
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Base, engine
from services.weather_service import WeatherService
from mqtt_client import start_mqtt_thread
from sqlalchemy import text
from api.api import api_router
from web.views import router as web_router
import models


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

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(web_router)

app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.get("/api/weather/irrigation-check")
async def check_irrigation_status():
    summary = await WeatherService.get_irrigation_summary()
    if summary is None:
        raise HTTPException(status_code=503, detail="Hava durumu servisine ulaşılamıyor.")
    return {"status": "success", "data": summary}

@app.get("/api/irrigation/decision")
async def get_irrigation_decision():
    summary = await WeatherService.get_irrigation_summary()
    if not summary:
        raise HTTPException(status_code=500, detail="Hava durumu verisi eksik.")
    return {"decision": "Wait", "reason": "Rain expected soon"}