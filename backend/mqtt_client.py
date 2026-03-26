import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from config import MQTT_BROKER, MQTT_PORT, TOPIC_SENSOR, TOPIC_COMMAND 
from database import SessionLocal
from db_utils import save_sensor_data, get_field_location
from decision import DecisionLogic
from services.weather_service import WeatherService
import models

def on_connect(client, userdata, flags, rc):
    print(f"MQTT: Broker'a bağlandı! Kod: {rc}")
    client.subscribe(TOPIC_SENSOR)
    

def on_message(client, userdata, msg):
    db = SessionLocal()
    try:
        payload = json.loads(msg.payload.decode())
        lora_id = payload.get("lora_id")
        moisture_value = payload.get("value")
        
        print(f"Veri Geldi -> Node: {lora_id}, Nem: %{moisture_value}")

        if lora_id and moisture_value is not None:
            node = save_sensor_data(lora_id, moisture_value, db)
            if node is None:
                print(f"Hata: {lora_id} ID'li cihaz kayıtlı değil!")
                return
            
            location = get_field_location(node.field_id, db)
            
            pump_status = DecisionLogic.decide_irrigation(float(moisture_value), location)
            print(f"Karar Verildi: {pump_status}")
            
            komut_paketi = f"{lora_id}:{pump_status}"
            print(f"Komut MQTT'ye ({TOPIC_COMMAND}) basıldı: {komut_paketi}")

    except Exception as e:
        print(f"MQTT Veri İşleme Hatası: {e}")
        db.rollback()
    finally:
        db.close()

def start_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT Connection Error: {e}")

def start_mqtt_thread():
    threading.Thread(target=start_mqtt, daemon=True).start()