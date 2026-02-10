import time
import json
from umqtt.simple import MQTTClient
import network_config  # wifi_baglan burada
import config          # Tüm ayarlar burada
from sensors import SensorManager

sm = SensorManager(config.DHT_PIN)

def sub_cb(topic, msg):
    try:
        print(f"Yeni Komut Geldi [{topic}]: {msg}")
        data = json.loads(msg)
        
        if data.get('watering') == True:
            print(">>> SULAMA BAŞLADI!")
        else:
            print(">>> SULAMA DURDURULDU!")
    except Exception as e:
        print("Komut işleme hatası:", e)


if network_config.wifi_baglan():
    client = MQTTClient(config.CLIENT_ID, config.MQTT_SERVER)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(config.TOPIC_SUB)
    
    last_publish = 0
    
    while True:
        client.check_msg()
        
        if (time.time() - last_publish) >= 10:
            data = sm.get_data()
            if data:
                data["device_id"] = config.CLIENT_ID
                client.publish(config.TOPIC_PUB, json.dumps(data))
                print("Veri gönderildi:", data)
            last_publish = time.time()
        
        time.sleep(0.1)
