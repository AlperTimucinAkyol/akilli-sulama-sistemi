from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse          
from fastapi.staticfiles import StaticFiles         
from fastapi.templating import Jinja2Templates       
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Base, engine
from services.weather_service import WeatherService
from mqtt_client import start_mqtt_thread
from lora_service import LoRaGateway ##### GEÇİÇİ YORUMA ALINDI RASPI'DE AÇILMALI #####
from sqlalchemy import text
from api.api import api_router
from web.views import router as web_router
import offline_queue as oq
from sync_worker import start_sync_worker
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # SQLite offline kuyruğu başlat
    oq.init_queue()

    # PostgreSQL bağlantısını ve tablo oluşturmayı dene
    # DB kapalıysa uygulama yine başlar; sync worker DB açılınca devreye girer
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("DB bağlantısı başarılı, tablolar oluşturuluyor...")
        Base.metadata.create_all(engine)
        print("Tablolar hazır.")
    except Exception as e:
        print(f"DB bağlantısı hatası (uygulama offline modda devam ediyor): {e}")
        
    print("MQTT başlatılıyor...")
    start_mqtt_thread()

    # Offline kuyruk sync worker'ını başlat
    start_sync_worker()
    print("Offline kuyruk sync worker başlatıldı.")
    
    
    ##### GEÇİÇİ YORUMA ALINDI RASPI'DE AÇILMALI #####
    app.state.lora_gw = LoRaGateway()
    app.state.lora_gw.start_in_thread()
    print("LoRa Gateway arka planda başlatıldı.")
    # print("LoRa Gateway başlatılıyor...")
    # lora_gw = LoRaGateway()
    # lora_gw.start_in_thread()

    yield
    app.state.lora_gw._cleanup()

app = FastAPI(lifespan=lifespan)

current_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")
print(static_dir)
# Mount işlemini bu tam yol ile yapalım
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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