/*
 * ============================================================
 *  Akıllı Sulama Sistemi — ESP32 LoRa Firmware
 *  Modül : EBYTE E22-900T22D (SX1262, UART tabanlı)
 *  Kütüphane: LoRa_E22 by xreef (Arduino Library Manager'dan kur)
 *  Platform : Arduino IDE + ESP32 board paketi
 * ============================================================
 *
 *  BAĞLANTI ŞEMASI (E22 <-> ESP32):
 * ┌─────────────┬──────────────┬─────────────────────────────┐
 * │  E22 Pin    │  ESP32 Pin   │  Açıklama                   │
 * ├─────────────┼──────────────┼─────────────────────────────┤
 * │  VCC        │  3.3V        │  Güç (3.3V !)               │
 * │  GND        │  GND         │  Toprak                     │
 * │  TXD        │  GPIO 16     │  ESP32 Serial2 RX           │
 * │  RXD        │  GPIO 17     │  ESP32 Serial2 TX           │
 * │  AUX        │  GPIO 18     │  Modül hazır sinyali        │
 * │  M0         │  GPIO 21     │  Mod seçimi                 │
 * │  M1         │  GPIO 19     │  Mod seçimi                 │
 * └─────────────┴──────────────┴─────────────────────────────┘
 *
 *  Toprak Nemi Sensörü (Kapasitif, analog çıkışlı):
 *  Sensör AO  → ESP32 GPIO 34 (ADC1_CH6)
 *  Sensör VCC → 3.3V
 *  Sensör GND → GND
 *
 *  Röle / Sulama Vanası:
 *  IN1  → ESP32 GPIO 26
 *
 *  KURULUM:
 *  1. Arduino IDE > Kütüphane Yöneticisi > "LoRa_E22" ara > Renzo Mischiat tarafından yükle
 *  2. Araçlar > Board > "ESP32 Dev Module" seç
 *  3. Bu .ino dosyasını yükle
 * ============================================================
 */

#include <Arduino.h>
#include "LoRa_E22.h"

#define LORA_RX_PIN  16
#define LORA_TX_PIN  17
#define LORA_AUX_PIN 18
#define LORA_M0_PIN  21
#define LORA_M1_PIN  19

#define NODE_ID          "esp32_tarla_1"
#define SEND_INTERVAL_MS 15000 

HardwareSerial loraSerial(2);
LoRa_E22 lora(&loraSerial, LORA_AUX_PIN, LORA_M0_PIN, LORA_M1_PIN, UART_BPS_RATE_9600);

struct SensorPacket {
    char node_id[20];
    float soil_moisture;
    int   raw_adc;
    bool  pump_on;
} __attribute__((packed));


struct CommandPacket {
    char  node_id[20];
    uint8_t pump_cmd; 
}__attribute__((packed));

unsigned long lastSendTime = 0;
bool pumpState = false;
float simulatedMoisture = 45.0;

float readSoilMoisture(int *rawOut) {
    if (pumpState) simulatedMoisture += 0.5;
    else simulatedMoisture -= 0.2;
    
    if (simulatedMoisture > 90.0) simulatedMoisture = 90.0;
    if (simulatedMoisture < 20.0) simulatedMoisture = 20.0;

    if (rawOut) *rawOut = map(simulatedMoisture, 0, 100, 3200, 1500);
    return simulatedMoisture;
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
    pkt.raw_adc       = rawAdc;
    pkt.pump_on       = pumpState;

    // DÜZELTME: Verinin adresini ve boyutunu gönderiyoruz
    ResponseStatus rs = lora.sendMessage(&pkt, sizeof(SensorPacket));

    Serial.print("[LORA] Gönderiliyor -> Nem: %");
    Serial.print(moisture, 1);
    Serial.print(" | Durum: ");
    Serial.println(rs.getResponseDescription());
}

void checkIncoming() {
    if (!lora.available()) return;

    ResponseStructContainer rsc = lora.receiveMessage(sizeof(CommandPacket));
    if (rsc.status.code != E22_SUCCESS) {
        rsc.close();
        return;
    }

    CommandPacket *cmd = (CommandPacket*)rsc.data;

    if (strcmp(cmd->node_id, NODE_ID) == 0) {
        pumpState = (cmd->pump_cmd == 1);
        Serial.print("[LORA] Komut Alındı -> Pompa Durumu: ");
        Serial.println(pumpState ? "Sanal Olarak AÇILDI" : "Sanal Olarak KAPATILDI");
    }

    rsc.close();
}

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n--- AGROLOG SENSOR NODE (SIMULASYON) ---");

    if (!initLoRa()) {
        Serial.println("[HATA] LoRa modülü başlatılamadı!");
        while (true) { delay(1000); }
    }

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