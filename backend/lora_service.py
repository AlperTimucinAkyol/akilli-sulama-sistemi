"""
============================================================
 Akıllı Sulama Sistemi — Raspberry Pi LoRa Gateway Servisi
 Modül  : EBYTE E22-900T22D (SX1262, UART tabanlı)
 Kütüphane: ebyte-lora-e22-rpi  (pip install ebyte-lora-e22-rpi)
 Dosya  : backend/lora_service.py
============================================================

 BAĞLANTI ŞEMASI (E22 <-> Raspberry Pi 4):
 ┌─────────────┬──────────────────┬──────────────────────────┐
 │  E22 Pin    │  Raspberry Pi    │  Açıklama               │
 ├─────────────┼──────────────────┼──────────────────────────┤
 │  VCC        │  Pin 1  (3.3V)   │  Güç (3.3V !)           │
 │  GND        │  Pin 6  (GND)    │  Toprak                  │
 │  TXD        │  Pin 10 (GPIO15) │  Pi UART RX (BCM 15)    │
 │  RXD        │  Pin 8  (GPIO14) │  Pi UART TX (BCM 14)    │
 │  AUX        │  Pin 12 (GPIO18) │  Modül hazır sinyali    │
 │  M0         │  Pin 16 (GPIO23) │  Mod seçimi              │
 │  M1         │  Pin 18 (GPIO24) │  Mod seçimi              │
 └─────────────┴──────────────────┴──────────────────────────┘

 RASPBERRY PI UART AKTİFLEŞTİRME (bir kez yapılır):
   sudo raspi-config
   → Interface Options → Serial Port
   → "Login shell over serial?" → NO
   → "Serial hardware enabled?" → YES
   → Reboot

 GEREKLİ PAKETLER:
   pip install ebyte-lora-e22-rpi pyserial paho-mqtt RPi.GPIO
   (veya: pip install -r requirements.txt)
============================================================
"""

import json
import struct
import time
import threading
import logging
import serial

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("[LORA] RPi.GPIO bulunamadı — geliştirme modunda çalışılıyor.")

import paho.mqtt.client as mqtt
from config import Config

# ─────────────────────────────────
# GPIO & UART Ayarları
# ─────────────────────────────────
SERIAL_PORT  = "/dev/serial0"   # Pi'nin donanım UART'ı (veya /dev/ttyS0)
BAUD_RATE    = 9600
AUX_PIN      = 18   # BCM numarası
M0_PIN       = 23
M1_PIN       = 24

# ─────────────────────────────────
# Sensör Paketi Yapısı (ESP32 ile aynı sıra!)
# struct format: 20s f i ?  = node_id(20 byte) + float(4) + int(4) + bool(1)
SENSOR_FMT   = "20s f i ?"
SENSOR_SIZE  = struct.calcsize(SENSOR_FMT)   # = 29 byte

# Komut Paketi Yapısı
CMD_FMT      = "20s B"          # node_id(20) + pump_cmd(1 byte)
CMD_SIZE     = struct.calcsize(CMD_FMT)

# ─────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("lora_service")


class LoRaGateway:
    """
    Raspberry Pi üzerinde EBYTE E22-900T22D modülünü yöneten gateway sınıfı.
    - UART üzerinden ESP32 LoRa node'larından sensör verisi alır
    - MQTT'ye publish eder
    - MQTT'den gelen komutları LoRa aracılığıyla ESP32'ye iletir
    """

    def __init__(self):
        self.ser: serial.Serial = None
        self.mqtt_client = None
        self._running = False
        self._lock = threading.Lock()

    # ── GPIO & UART başlatma ──────────────────────────────────
    def _init_gpio(self):
        if not RPI_AVAILABLE:
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # Normal mod: M0=LOW, M1=LOW
        GPIO.setup(M0_PIN,  GPIO.OUT)
        GPIO.setup(M1_PIN,  GPIO.OUT)
        GPIO.setup(AUX_PIN, GPIO.IN)
        GPIO.output(M0_PIN, GPIO.LOW)
        GPIO.output(M1_PIN, GPIO.LOW)
        log.info("GPIO başarıyla yapılandırıldı (Normal mod).")

    def _wait_aux_high(self, timeout=3.0):
        """AUX pini HIGH olana kadar bekle (modül hazır sinyali)."""
        if not RPI_AVAILABLE:
            return
        deadline = time.time() + timeout
        while time.time() < deadline:
            if GPIO.input(AUX_PIN) == GPIO.HIGH:
                return
            time.sleep(0.01)
        log.warning("AUX HIGH bekleme zaman aşımına uğradı!")

    def _open_serial(self):
        self.ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )
        log.info(f"Serial port açıldı: {SERIAL_PORT} @ {BAUD_RATE} baud")

    # ── Veri Alma ────────────────────────────────────────────
    def _read_packet(self):
        self._wait_aux_high()
        raw = self.ser.read(SENSOR_SIZE)
        if len(raw) < SENSOR_SIZE:
            return None
        try:
            node_id_b, moisture, raw_adc, pump_on = struct.unpack(SENSOR_FMT, raw)
            # NUL karakterlerini temizleyerek decode et
            node_id = node_id_b.split(b'\x00')[0].decode("utf-8", errors="ignore")
            
            # Veri çok saçma gelmişse (kayma varsa) reddet
            if not node_id or len(node_id) < 3:
                raise struct.error("Geçersiz Node ID")
                
            return {
                "lora_id":      node_id,
                "value":        round(moisture, 2),
                "raw_adc":      raw_adc,
                "pump_on":      bool(pump_on)
            }
        except Exception as e:
            # Kayma olduğunda tamponu boşaltıp bir sonraki paketi bekle
            self.ser.reset_input_buffer()
            return None

    # ── Komut Gönderme ────────────────────────────────────────
    def send_command(self, node_id: str, pump_on: bool):
        if self.ser is None or not self.ser.is_open:
            log.error("Serial port kapalı!")
            return

        self._wait_aux_high()
        payload = struct.pack(CMD_FMT,
                              node_id.encode("utf-8").ljust(20, b"\x00"),
                              1 if pump_on else 0)
        with self._lock:
            self.ser.write(payload)
            self.ser.flush() # Verinin tamamen gittiğinden emin ol
        log.info(f"Komut gönderildi -> {node_id} | Pompa: {'AÇ' if pump_on else 'KAPAT'}")
        
        # KRİTİK: Komuttan sonra girişte kalan çöp verileri temizle
        time.sleep(0.1) 
        self.ser.reset_input_buffer()

    # ── MQTT ─────────────────────────────────────────────────
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            log.info(f"MQTT Broker'a bağlandı.")
            client.subscribe(Config.TOPIC_COMMAND)
        else:
            log.error(f"MQTT bağlantı hatası, kod: {rc}")

    def _on_mqtt_message(self, client, userdata, msg):
        """
        MQTT'den gelen komutları ESP32'ye ilet.
        Beklenen format (JSON):  {"node_id": "esp32_tarla_1", "pump": true}
        """
        try:
            data = json.loads(msg.payload.decode())
            node_id = data.get("node_id", "")
            pump_on = bool(data.get("pump", False))
            log.info(f"MQTT Komut → LoRa'ya iletiliyor | Node: {node_id} Pompa: {pump_on}")
            self.send_command(node_id, pump_on)
        except Exception as e:
            log.error(f"MQTT mesaj işleme hatası: {e}")

    def _init_mqtt(self):
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        self.mqtt_client.loop_start()
        log.info("MQTT client başlatıldı.")

    # ── Ana Döngü ─────────────────────────────────────────────
    def run(self):
        log.info("=" * 50)
        log.info(" LoRa Gateway Başlatılıyor...")
        log.info("=" * 50)

        self._init_gpio()
        self._open_serial()
        self._init_mqtt()

        self._running = True
        log.info("ESP32 node'larından veri bekleniyor...")

        try:
            while self._running:
                if self.ser.in_waiting >= SENSOR_SIZE:
                    packet = self._read_packet()
                    if packet:
                        payload_str = json.dumps(packet)
                        self.mqtt_client.publish(Config.TOPIC_SENSOR, payload_str)
                        log.info(f"ESP32 → Backend: {payload_str}")
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.ser.reset_input_buffer()
            log.info("Kullanıcı tarafından durduruldu.")
        finally:
            self._cleanup()

    def _cleanup(self):
        self._running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        if self.ser and self.ser.is_open:
            self.ser.close()
        if RPI_AVAILABLE:
            GPIO.cleanup()
        log.info("LoRa Gateway kapatıldı.")

    def start_in_thread(self):
        """FastAPI lifespan içinden thread olarak başlatmak için."""
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        return t


# ── Standalone çalıştırma ─────────────────────────────────────
if __name__ == "__main__":
    gateway = LoRaGateway()
    gateway.run()
