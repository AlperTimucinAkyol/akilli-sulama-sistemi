import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from config import MQTT_BROKER, MQTT_PORT, TOPIC_SENSOR
from database import SessionLocal
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
            node = db.query(models.Node).filter(models.Node.lora_id == lora_id).first()
            
            if not node:
                print(f"Hata: {lora_id} ID'li cihaz veritabanında kayıtlı değil!")
                return

            # Bu cihaza bağlı sensörü bul
            sensor = db.query(models.Sensor).filter(
                models.Sensor.node_id == node.id,
                models.Sensor.sensor_type == "Soil Moisture"
            ).first()

            if not sensor:
                print(f"Bilgi: {lora_id} için 'Soil Moisture' sensörü bulunamadı. Oluşturuluyor...")
                sensor = models.Sensor(node_id=node.id, sensor_type="Soil Moisture", created_at=datetime.now())
                db.add(sensor)
                db.commit()
                db.refresh(sensor)

            new_data = models.SensorData(
                sensor_id=sensor.id,
                value=float(moisture_value),
                timestamp=datetime.now()
            )
            db.add(new_data)
            
            # 5. Node'un 'last_seen' bilgisini güncelle
            node.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            db.commit()
            print(f"Veritabanına kaydedildi. Sensor ID: {sensor.id}")

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