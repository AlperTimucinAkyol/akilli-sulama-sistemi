import paho.mqtt.client as mqtt
import json
import logging
import threading
import asyncio  # Asenkron fonksiyonu çalıştırmak için eklendi
from datetime import datetime
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from models.iot import IrrigationLog
from config import Config
from database import SessionLocal
from db_utils import save_sensor_data, get_field_location
from decision import DecisionLogic, DEFAULT_RULE # Varsayılan kuralı import ettik
import offline_queue as oq

logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"MQTT: Broker'a başarıyla bağlandı!")
        client.subscribe(Config.TOPIC_SENSOR)
    else:
        print(f"MQTT: Bağlantı hatası! Kod: {rc}")

async def _process_message_async(lora_id: str, moisture_value: float, temp_value: float, db):
    """
    Asenkron karar mekanizmasını çalıştırır ve verileri kaydeder.
    Geriye sulama kararını (True/False) döndürür.
    """
    # 1. Sensör verisini kaydet ve node bilgisini al
    node = save_sensor_data(lora_id, moisture_value, db)
    if node is None:
        logger.warning(f"Hata: {lora_id} ID'li cihaz kayıtlı değil!")
        return False

    location = get_field_location(node.field_id, db)

    # 2. KARAR MEKANİZMASI (Yeni asenkron yapı)
    # Eğer ESP32 sıcaklık göndermiyorsa, 25.0 gibi bir değer veya hava durumu verisi paslanabilir.
    decision = await DecisionLogic.decide_irrigation(
        db=db,
        field_id=node.field_id,
        current_moisture=moisture_value,
        current_temp=temp_value,
        location=location
    )
    
    pump_on = (decision == "ON")
    logger.info(f"Karar Verildi: {'SULAMA AÇ' if pump_on else 'SULAMA KAPAT'}")

    # 3. Log Kaydı
    log = IrrigationLog(
        field_id=node.field_id,
        node_id=node.id,
        action=pump_on,
        mode=True, # Otomatik Mod
        soil_moisture=float(moisture_value),
        decision_note=(
            f"Nem: %{moisture_value}, Sıcaklık: {temp_value}°C, Konum: {location}, "
            f"Karar: {decision}"
        ),
        timestamp=datetime.now(),
    )
    db.add(log)
    db.commit()
    return pump_on


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        lora_id = payload.get("lora_id")
        moisture_value = float(payload.get("value", 0))
        # ESP32'den 'temp' gelmiyorsa varsayılan 25 derece kabul et
        temp_value = float(payload.get("temp", 25.0)) 
    except Exception as e:
        logger.error(f"MQTT payload parse hatası: {e}")
        return

    logger.info(f"Veri Geldi -> Node: {lora_id}, Nem: %{moisture_value}, Sıcaklık: {temp_value}°C")

    # Karar değişkenini varsayılan olarak güvenli moda (KAPALI) alalım
    final_pump_status = False

    # ── PostgreSQL pipeline'ı ─────────────────────────────────────────
    db = SessionLocal()
    try:
        # Senkron MQTT callback'i içinde ASENKRON fonksiyonu çalıştırıyoruz
        final_pump_status = asyncio.run(_process_message_async(lora_id, moisture_value, temp_value, db))

    except (OperationalError, SQLAlchemyError) as e:
        db.rollback()
        logger.warning(f"[Fallback] DB Hatası, veri SQLite kuyruğuna alınıyor: {e}")
        oq.enqueue(lora_id, moisture_value)
        
        # DB yoksa en azından varsayılan nem eşiğine göre basit karar ver
        final_pump_status = moisture_value < DEFAULT_RULE["min_soil_moisture"]

    except Exception as e:
        db.rollback()
        logger.error(f"MQTT İşleme Hatası: {e}")
    finally:
        db.close()

    # ── Komutu ESP32'ye gönder (Her durumda) ──────────────────────────
    komut = json.dumps({
        "node_id": lora_id, 
        "pump": final_pump_status,
    })
    client.publish(Config.TOPIC_COMMAND, komut)
    logger.info(f"Komut Gönderildi -> {Config.TOPIC_COMMAND}: {komut}")

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
