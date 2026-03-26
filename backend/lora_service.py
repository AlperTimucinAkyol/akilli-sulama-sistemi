import serial, json, time
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, TOPIC_SENSOR, TOPIC_COMMAND

ser = serial.Serial('/dev/serial0', 9600, timeout=1)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

def on_mqtt_message(client, userdata, msg):
    if msg.topic == TOPIC_COMMAND:
        komut = msg.payload.decode()
        print(f"Backend'den emir geldi -> ESP32'ye gönderiliyor: {komut}")

        ser.write(f"{komut}\n".encode())

client.on_message = on_mqtt_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

client.subscribe(TOPIC_COMMAND)
client.loop_start()

print("LoRa Gateway Çalışıyor... (ESP32'den veri bekleniyor)")

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                try:
                    parts = line.split(',')
                    payload = json.dumps({"lora_id": parts[0], "value": float(parts[1])})
                    
                    client.publish(TOPIC_SENSOR, payload)
                    print(f"ESP32 -> Backend: {payload}")
                except Exception as e:
                    print(f"Format Hatası: {line} -> {e}")
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    ser.close()