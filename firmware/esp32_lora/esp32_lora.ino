#include "LoRa_E22.h"
#include <Arduino.h>

#define LORA_RX_PIN 16
#define LORA_TX_PIN 17
#define LORA_AUX_PIN 18
#define LORA_M0_PIN 21
#define LORA_M1_PIN 19

#define NODE_ID "esp32_tarla_2"
#define SEND_INTERVAL_MS 15000

#define SOIL_SENSOR_PIN 34

// Kalibrasyon değerleri (sensörünüzü test ederek bulmanız gereken değerler)
// Örnek değerler - siz kendi sensörünüzü kalibre edin!
#define AIR_VALUE 3200   // Sensör kupkuruyken okunan değer
#define WATER_VALUE 1100 // Sensör tamamen ıslakken okunan değer

#define RELAY_IN1_PIN 26 // Pompa kontrolü

HardwareSerial loraSerial(2);
LoRa_E22 lora(&loraSerial, LORA_AUX_PIN, LORA_M0_PIN, LORA_M1_PIN,
              UART_BPS_RATE_9600);

struct SensorPacket {
  char node_id[20];
  float soil_moisture;
  int32_t raw_adc; // 4 byte (Sabit 32-bit)
  uint8_t pump_on;
} __attribute__((packed));

struct CommandPacket {
  char node_id[20];
  uint8_t pump_cmd;
} __attribute__((packed));

unsigned long lastSendTime = 0;
bool pumpState = false;
float simulatedMoisture = 45.0;

float readSoilMoisture(int *rawOut) {
  // 1. ADC değerini oku (ESP32 12-bit: 0-4095 arası)
  int rawAdc = analogRead(SOIL_SENSOR_PIN);

  // 2. İsteğe bağlı: Hareketli ortalama ile gürültüyü azalt
  static int readings[5] = {0};
  static int readIndex = 0;
  static int total = 0;

  total = total - readings[readIndex];
  readings[readIndex] = rawAdc;
  total = total + readings[readIndex];
  readIndex = (readIndex + 1) % 5;
  int filteredAdc = total / 5;

  // 3. Ham ADC değerini yüzdeye dönüştür
  // Not: Kapasitif sensörlerde kuru havada yüksek değer, suda düşük değer
  // alınır Bu nedenle map fonksiyonunu ters kullanıyoruz
  float moisturePercent = 0.0;

  if (filteredAdc >= AIR_VALUE) {
    moisturePercent = 0.0; // Çok kuru
  } else if (filteredAdc <= WATER_VALUE) {
    moisturePercent = 100.0; // Çok ıslak
  } else {
    // Linear interpolasyon: Yüksek ADC = Düşük nem
    moisturePercent = map(filteredAdc, AIR_VALUE, WATER_VALUE, 0, 100);
  }

  // 4. Değeri sınırla (güvenlik için)
  moisturePercent = constrain(moisturePercent, 0.0, 100.0);

  // 5. Raw değeri döndür (isteğe bağlı)
  if (rawOut) {
    *rawOut = filteredAdc;
  }

  // 6. Debug çıktısı (isteğe bağlı - Serial monitor için)
  static unsigned long lastDebugPrint = 0;
  if (millis() - lastDebugPrint > 5000) { // Her 5 saniyede bir yazdır
    Serial.print("[SENSOR] Raw ADC: ");
    Serial.print(filteredAdc);
    Serial.print(" | Nem: %");
    Serial.println(moisturePercent, 1);
    lastDebugPrint = millis();
  }

  return moisturePercent;
}

bool initLoRa() {
  loraSerial.begin(9600, SERIAL_8N1, LORA_RX_PIN, LORA_TX_PIN);
  // DÜZELTME: ResponseStatus yerine bool kontrolü yapıyoruz
  bool status = lora.begin();
  if (!status) {
    return false;
  }
  Serial.println("[LORA] Modül başarıyla başlatıldı.");
  return true;
}

void sendSensorData() {
  int rawAdc;
  float moisture = readSoilMoisture(&rawAdc);

  SensorPacket pkt;
  strncpy(pkt.node_id, NODE_ID, sizeof(pkt.node_id));
  pkt.soil_moisture = moisture;
  pkt.raw_adc = rawAdc;
  pkt.pump_on = pumpState;

  // DÜZELTME: Verinin adresini ve boyutunu gönderiyoruz
  ResponseStatus rs = lora.sendMessage(&pkt, sizeof(SensorPacket));

  Serial.print("[LORA] Gönderiliyor -> Nem: %");
  Serial.print(moisture, 1);
  Serial.print(" | Durum: ");
  Serial.println(rs.getResponseDescription());

  // EMI toparlanma: gönderme başarısız olduysa LoRa modülünü yeniden başlat
  if (rs.code != E22_SUCCESS) {
    Serial.println("[LORA] Gönderme hatasi! Modül yeniden baslatiliyor...");
    delay(500);
    if (initLoRa()) {
      Serial.println("[LORA] Modül yeniden baslatildi.");
    } else {
      Serial.println("[LORA] Yeniden baslatma basarisiz.");
    }
  }
}

void checkIncoming() {
  if (!lora.available())
    return;

  ResponseStructContainer rsc = lora.receiveMessage(sizeof(CommandPacket));
  if (rsc.status.code != E22_SUCCESS) {
    rsc.close();
    return;
  }

  CommandPacket *cmd = (CommandPacket *)rsc.data;

  if (strcmp(cmd->node_id, NODE_ID) == 0) {
    pumpState = (cmd->pump_cmd == 1);
    Serial.print("[LORA] Komut Alindi -> Pompa: ");
    Serial.println(pumpState ? "ACILDI" : "KAPATILDI");

    digitalWrite(RELAY_IN1_PIN, pumpState ? LOW : HIGH);
    Serial.print("[ROLE] Role: ");
    Serial.println(pumpState ? "KAPAL (pompa calisiyor)" : "ACIK (pompa durdu)");

    // EMI toparlanma: role/pompa gecis gurultusunun LoRa'yi etkilememesi icin bekle
    delay(200);
  }

  rsc.close();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n--- AGROLOG SENSOR NODE (SIMULASYON) ---");

  // LoRa baslatma: basarisiz olursa retry yap, 5 denemede ESP32'yi yeniden basklat
  int loraRetry = 0;
  while (!initLoRa()) {
    loraRetry++;
    Serial.print("[HATA] LoRa baslatma basarisiz. Deneme: ");
    Serial.println(loraRetry);
    delay(3000);
    if (loraRetry >= 5) {
      Serial.println("[HATA] LoRa baslatılamadi, ESP32 yeniden baslatiliyor...");
      ESP.restart();
    }
  }

  // EKLENECEK — setup() içine
  // KRITIK: pinMode'dan ONCE HIGH yaz — yoksa röle başlatmada kısa süre açılır
  digitalWrite(RELAY_IN1_PIN, HIGH);
  pinMode(RELAY_IN1_PIN, OUTPUT);

  sendSensorData();
  lastSendTime = millis();
}

void loop() {
  checkIncoming();

  if (millis() - lastSendTime >= SEND_INTERVAL_MS) {
    sendSensorData();
    lastSendTime = millis();
  }
  delay(100);
}