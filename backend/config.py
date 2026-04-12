import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    TOPIC_SENSOR = "lora/data"
    TOPIC_COMMAND = "lora/komut"

    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 günlük

    DATABASE_URL = os.getenv("DATABASE_URL")