from fastapi import FastAPI
import psycopg2
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import threading

app = FastAPI()

# --- AYARLAR ---
DB_CONFIG = {
    "dbname": "EspSensorDb",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SENSOR = "esp32/sensor"
TOPIC_COMMAND = "esp32/komut"

# --- KARAR MEKANİZMASI ---
def decision_logic(humidity: float, last_state: bool) -> bool:
    if humidity < 55 and not last_state:
        return True
    if humidity > 65 and last_state:
        return False
    return last_state

# --- MQTT OLAYLARI ---
def on_connect(client, userdata, flags, rc):
    print(f"MQTT Broker'a bağlandı! Sonuç kodu: {rc}")
    client.subscribe(TOPIC_SENSOR)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("device_id")
        temp = payload.get("temperature")
        hum = payload.get("humidity")
        
        print(f"Veri geldi -> Cihaz: {device_id}, Sıcaklık: {temp}, Nem: %{hum}")

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT d.decision FROM decisions d
            JOIN measurements m ON d.measurement_id = m.id
            WHERE m.device_id = %s ORDER BY d.created_at DESC LIMIT 1
        """, (device_id,))

        row = cur.fetchone()
        last_state = row[0] if row else False

        new_state = decision_logic(hum, last_state)
        reason = "durum degismedi" if new_state == last_state else "nem esigi asildi"

        cur.execute("INSERT INTO measurements (device_id, temperature, humidity) VALUES (%s, %s, %s) RETURNING id",
                    (device_id, temp, hum))
        m_id = cur.fetchone()[0]

        cur.execute("INSERT INTO decisions (measurement_id, decision, reason) VALUES (%s, %s, %s)",
                    (m_id, new_state, reason))

        conn.commit()
        cur.close()
        conn.close()

        response_data = {"watering": new_state, "reason": reason}
        client.publish(TOPIC_COMMAND, json.dumps(response_data))
        print(f"Komut gönderildi: {new_state}")

    except Exception as e:
        print(f"Hata oluştu: {e}")

# --- MQTT'Yİ AYRI BİR THREAD'DE BAŞLAT ---
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

threading.Thread(target=start_mqtt, daemon=True).start()