import time
import json
from umqtt.simple import MQTTClient
import network_config
import config 
from sensors import SensorManager


sm = SensorManager(config.MOISTURE_PIN)

def sub_cb(topic, msg):
    """MQTT'den gelen komutları karşılayan callback fonksiyonu"""
    try:
        topic_str = topic.decode('utf-8')
        msg_str = msg.decode('utf-8')
        print(f"--- [KOMUT ALINDI] ---")
        print(f"Topic: {topic_str}\nMesaj: {msg_str}")
        
        data = json.loads(msg_str)
        
        # Sulama komutu kontrolü
        if data.get('watering') is True:
            # Burada bir röleyi tetikleyebilirsin
            print(">>> EYLEM: Sulama Sistemi ACILDI!")
        elif data.get('watering') is False:
            print(">>> EYLEM: Sulama Sistemi KAPATILDI!")
            
    except Exception as e:
        print("Komut işleme hatası:", e)

def connect_mqtt():
    """MQTT Broker'a bağlanır ve topic'lere abone olur"""
    try:
        client = MQTTClient(
            config.CLIENT_ID, 
            config.MQTT_SERVER, 
            keepalive=60
        )
        client.set_callback(sub_cb)
        client.connect()
        client.subscribe(config.TOPIC_SUB)
        print("MQTT: Broker'a bağlandı ve abone olundu.")
        return client
    except Exception as e:
        print("MQTT: Bağlantı kurulamadı, tekrar denenecek...", e)
        return None

def main():
    print("--- Sistem Baslatiliyor ---")
    
    # 1. WiFi Bağlantısı
    if not network_config.wifi_baglan():
        print("Kritik Hata: WiFi baglanamadigi icin sistem durduruldu.")
        return

    # 2. MQTT Başlatma
    client = connect_mqtt()
    last_publish = 0
    publish_interval = 10  # 10 saniyede bir veri gönder

    print("--- Dongu Baslatildi ---")
    
    while True:
        try:
            if client is None:
                print("Baglanti yok, yeniden deneniyor...")
                client = connect_mqtt()
                if client is None:
                    time.sleep(5)
                    continue

            # MQTT mesajları kontrol ediliyor
            client.check_msg()

            current_time = time.time()
            if (current_time - last_publish) >= publish_interval:
                sensor_reading = sm.get_data()
                
                if sensor_reading:
                    payload = {
                        "lora_id": config.CLIENT_ID,
                        "value": sensor_reading["soil_moisture"],
                        "raw_value": sensor_reading["raw_value"]
                    }
                    
                    client.publish(config.TOPIC_PUB, json.dumps(payload))
                    print(f"Veri Gönderildi: {payload}")
                    
                last_publish = current_time

        except OSError as e:
            print("Ağ hatası oluştu, yeniden bağlanılıyor...", e)
            client = None  # sonraki döngüde yeniden bağlanmayı tetikler
        except Exception as e:
            print("Beklenmedik hata:", e)
            time.sleep(2)

        time.sleep(0.1)


if __name__ == "__main__":
    main()
