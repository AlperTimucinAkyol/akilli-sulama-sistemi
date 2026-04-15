import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from config import Config
from database import SessionLocal
from db_utils import save_sensor_data, get_field_location
from decision import DecisionLogic
# from services.weather_service import WeatherService # Şu an gerekmiyorsa kalsın
import models

def on_connect(client, userdata, flags, rc, properties=None): # v2'de properties eklendi
    if rc == 0:
        print(f"MQTT: Broker'a başarıyla bağlandı!")
        client.subscribe(Config.TOPIC_SENSOR)
    else:
        print(f"MQTT: Bağlantı hatası! Kod: {rc}")

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
            
            # Veritabanından konumu al (Saha koordinatları vb.)
            location = get_field_location(node.field_id, db)
            
            # Sulama kararı ver (Nem % ve konuma göre)
            pump_on = DecisionLogic.decide_irrigation(float(moisture_value), location)
            print(f"Karar Verildi: {'SULAMA AÇ' if pump_on else 'SULAMA KAPAT'}")

            # Komutu ESP32'nin anlayacağı JSON formatına çevir
            komut = json.dumps({"node_id": lora_id, "pump": bool(pump_on)})
            client.publish(Config.TOPIC_COMMAND, komut)
            print(f"Komut MQTT'ye ({Config.TOPIC_COMMAND}) basıldı: {komut}")

    except Exception as e:
        print(f"MQTT Veri İşleme Hatası: {e}")
        db.rollback()
    finally:
        db.close()

def start_mqtt():
    # --- KRİTİK GÜNCELLEME: Paho v2.0+ için CallbackAPIVersion eklenmeli ---
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        print(f"MQTT: {Config.MQTT_BROKER}:{Config.MQTT_PORT} adresine bağlanılıyor...")
        mqtt_client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT Bağlantı Hatası: {e}")

def start_mqtt_thread():
    # Daemon=True: Ana program kapandığında bu thread de kapanır
    thread = threading.Thread(target=start_mqtt, daemon=True)
    thread.start()
    return thread
