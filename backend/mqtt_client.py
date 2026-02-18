import paho.mqtt.client as mqtt
import json
import threading
from config import MQTT_BROKER, MQTT_PORT, TOPIC_COMMAND, TOPIC_SENSOR
from decision import decision_logic
from database import get_connection

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

        conn = get_connection()
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


def start_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

def start_mqtt_thread():
    threading.Thread(target=start_mqtt, daemon=True).start()