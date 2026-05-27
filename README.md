<div align="center">

# 🌱 Sensör Destekli Akıllı Sulama Sistemi
### Sensor-Based Smart Irrigation System

*Otomatik Kontrol ve Kullanıcı Arayüzü Tasarımı / Automatic Control and User Interface Design*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129-009688.svg)](https://fastapi.tiangolo.com)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204-red.svg)](https://www.raspberrypi.com)
[![MCU](https://img.shields.io/badge/MCU-ESP32-orange.svg)](https://www.espressif.com)

**Karadeniz Teknik Üniversitesi · Of Teknoloji Fakültesi · Yazılım Mühendisliği Bölümü**  
*2025–2026 Bahar Dönemi Bitirme Projesi*

| | |
|---|---|
| **Öğrenciler / Students** | Alper Timuçin Akyol · Erdinç Topuz |
| **Danışman / Advisor** | Dr. Öğr. Üyesi Hakan AYDIN |

</div>

---

## 📖 İçindekiler / Table of Contents

- [Türkçe](#-türkçe)
  - [Proje Hakkında](#proje-hakkında)
  - [Sistem Mimarisi](#sistem-mimarisi)
  - [Donanım Bileşenleri](#donanım-bileşenleri)
  - [Kurulum](#kurulum)
  - [Kullanım](#kullanım)
- [English](#-english)
  - [About](#about)
  - [System Architecture](#system-architecture)
  - [Hardware Components](#hardware-components)
  - [Installation](#installation)
  - [Usage](#usage)

---

## 🇹🇷 Türkçe

### Proje Hakkında

Bu proje, küçük ve orta ölçekli tarım alanlarında su tüketimini optimize etmek amacıyla geliştirilmiş **IoT tabanlı akıllı bir sulama sistemi**dir. Sistem; gerçek zamanlı toprak nem ölçümü, meteorolojik veri entegrasyonu ve çok katmanlı karar mekanizmasıyla sulamayı otomatik olarak yönetmekte; web tabanlı gösterge paneli üzerinden uzaktan izleme ve manuel kontrol imkânı sunmaktadır.

**Temel Özellikler:**
- 📡 ESP32 + LoRa E22 ile uzun menzilli kablosuz sensör iletimi
- 🌦️ OpenWeather API entegrasyonu (yağış ve sıcaklık bariyerleri)
- 🗄️ PostgreSQL kalıcı depolama + SQLite çevrimdışı kuyruk (yüksek dayanıklılık)
- 🔐 JWT kimlik doğrulaması + bcrypt şifreleme
- 📊 Responsive Jinja2 web dashboard
- 🔄 Otomatik hata kurtarma ve fail-safe mekanizmaları

---

### Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                         UÇ BİRİM (ESP32)                        │
│  Kapasitif Nem Sensörü → ESP32 → Röle Modülü → Pompa           │
│                    ↕ LoRa E22 (29-byte binary paket)            │
└────────────────────────────┬────────────────────────────────────┘
                             │ LoRa (868/900 MHz)
┌────────────────────────────▼────────────────────────────────────┐
│                    MERKEZ (Raspberry Pi 4)                       │
│                                                                  │
│  LoRa Gateway ──→ MQTT Broker (Mosquitto) ──→ MQTT Client       │
│                                                    │             │
│                                              PostgreSQL          │
│                                                    │             │
│                                           Karar Motoru          │
│                                      (DecisionLogic)            │
│                                      + OpenWeather API          │
│                                                    │             │
│                                           FastAPI Backend        │
│                                                    │             │
│                                         Web Dashboard           │
│                                         (Jinja2 + HTML)         │
└─────────────────────────────────────────────────────────────────┘
```

**Karar Mekanizması Öncelik Hiyerarşisi:**

| Öncelik | Koşul | Sonuç |
|---------|-------|-------|
| 1 | Toprak nemi ≥ eşik değer (%25) | Pompa KAPALI |
| 2 | Sıcaklık ≥ maksimum (38°C) | Pompa KAPALI |
| 3 | Önümüzdeki 3 saatte yağış ≥ 1.0 mm | Pompa KAPALI |
| 4 | Tüm bariyerler aşıldı | Pompa AÇIK ✅ |

---

### Donanım Bileşenleri

| Bileşen | Model | Adet | Açıklama |
|---------|-------|------|----------|
| Mikrodenetleyici | ESP32 DevKit v1 | 1 | Uç birim kontrolcüsü |
| LoRa Modülü (Uç) | EBYTE E22-900T22D | 1 | Uç birim haberleşme |
| LoRa Modülü (Merkez) | EBYTE E22-900T22D | 1 | Raspberry Pi gateway |
| Merkezi Birim | Raspberry Pi 4 (4 GB) | 1 | Backend + gateway |
| Toprak Nem Sensörü | Kapasitif (3.3V) | 1 | Toprak nemi ölçümü |
| Röle Modülü | 5V Tek Kanal Optokuplörlü | 1 | Pompa anahtarlama |
| Li-ion Pil | 18650 3.7V ~3000 mAh | 2 | Uç birim güç kaynağı |
| Pil Yatağı | 2x18650 Seri Bağlantı | 1 | 7.4V nominal çıkış |

**LoRa E22 – Raspberry Pi 4 Bağlantı Tablosu:**

| E22 Pin | RPi Pini | BCM | Açıklama |
|---------|----------|-----|----------|
| VCC | Pin 1 | — | 3.3V |
| GND | Pin 6 | — | Toprak |
| TXD | Pin 10 | GPIO15 | UART RX |
| RXD | Pin 8 | GPIO14 | UART TX |
| AUX | Pin 12 | GPIO18 | Hazır sinyali |
| M0 | Pin 16 | GPIO23 | Mod seçimi |
| M1 | Pin 18 | GPIO24 | Mod seçimi |

---

### Kurulum

#### Ön Gereksinimler

- Raspberry Pi 4 (Raspberry Pi OS Lite önerilir)
- Python 3.10+
- PostgreSQL 14+
- Mosquitto MQTT Broker
- ESP32 için Arduino IDE

#### 1. Repoyu Klonla

```bash
git clone https://github.com/AlperTimucinAkyol/akilli-sulama-sistemi.git
cd akilli-sulama-sistemi
```

#### 2. PostgreSQL Kurulumu

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE USER sulama WITH PASSWORD 'sifreniz';"
sudo -u postgres psql -c "CREATE DATABASE sulama_db OWNER sulama;"
```

#### 3. MQTT Broker Kurulumu

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

#### 4. Backend Kurulumu

```bash
cd backend

# Sanal ortam oluştur (önerilir)
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Ortam değişkenlerini ayarla
cp .env.example .env
nano .env
```

`.env` dosyasında doldurulması gereken alanlar:

```env
DATABASE_URL=postgresql://sulama:sifreniz@localhost/sulama_db
SECRET_KEY=gizli-jwt-anahtari-buraya
OPENWEATHER_API_KEY=openweather-api-anahtariniz
MQTT_BROKER=localhost
MQTT_PORT=1883
LOCATION=Trabzon          # Hava durumu için şehir adı
```

#### 5. Backend'i Başlat

```bash
python main.py
# veya
uvicorn main:app --host 0.0.0.0 --port 8000
```

Dashboard'a erişmek için tarayıcıda `http://<raspberry-pi-ip>:8000` adresini aç.

#### 6. Raspberry Pi UART Etkinleştirme

```bash
sudo raspi-config
# Interface Options → Serial Port
# "login shell over serial" → No
# "serial port hardware" → Yes
sudo reboot
```

#### 7. ESP32 Firmware

1. Arduino IDE'yi aç
2. `firmware/esp32_lora/esp32_lora.ino` dosyasını aç
3. Gerekli kütüphaneleri yükle: `LoRa_E22` (Arduino Library Manager)
4. `esp32_lora.ino` içindeki `NODE_ID` değerini düzenle
5. ESP32'yi seç ve yükle

---

### Kullanım

**Otomatik Mod:** Sistem kurulduktan sonra sulama kararlarını otomatik olarak verir. Karar günlükleri dashboard'daki *Sulama Kayıtları* sayfasından takip edilebilir.

**Manuel Kontrol:** Dashboard üzerinden herhangi bir node için doğrudan pompa komutu gönderilebilir.

**Kural Özelleştirme:** Her tarla için *Tarla Detay* sayfasından özel sulama kuralları (nem eşiği, sıcaklık limiti, yağmur engeli) tanımlanabilir.

**API Dokümantasyonu:** `http://<ip>:8000/docs` adresinden otomatik oluşturulan Swagger UI'ya erişilebilir.

---

## 🇬🇧 English

### About

This project is an **IoT-based smart irrigation system** designed to optimize water consumption in small-to-medium-scale agricultural fields. The system autonomously manages irrigation through real-time soil moisture measurement, meteorological data integration, and a multi-layer decision mechanism, while providing remote monitoring and manual control via a web-based dashboard.

**Key Features:**
- 📡 Long-range wireless sensor transmission via ESP32 + LoRa E22
- 🌦️ OpenWeather API integration (rain and temperature barriers)
- 🗄️ PostgreSQL persistent storage + SQLite offline queue (high resilience)
- 🔐 JWT authentication + bcrypt password hashing
- 📊 Responsive Jinja2 web dashboard
- 🔄 Automatic error recovery and fail-safe mechanisms

---

### System Architecture

The system is organized into three layers:

- **Edge Layer:** ESP32 microcontroller reads capacitive soil moisture data, packages it into a 29-byte binary struct, and transmits it via LoRa E22 to the gateway.
- **Communication Layer:** LoRa E22 (868/900 MHz) point-to-point link + Mosquitto MQTT broker on Raspberry Pi.
- **Central Layer:** Raspberry Pi 4 runs the FastAPI backend, decision engine, PostgreSQL database, and Jinja2 web dashboard.

**Decision Priority Hierarchy:**

| Priority | Condition | Result |
|----------|-----------|--------|
| 1 | Soil moisture ≥ threshold (25%) | Pump OFF |
| 2 | Temperature ≥ maximum (38°C) | Pump OFF |
| 3 | Rain forecast ≥ 1.0 mm in 3 hours | Pump OFF |
| 4 | All barriers cleared | Pump ON ✅ |

---

### Hardware Components

| Component | Model | Qty | Purpose |
|-----------|-------|-----|---------|
| Microcontroller | ESP32 DevKit v1 | 1 | Edge node controller |
| LoRa Module (Edge) | EBYTE E22-900T22D | 1 | Edge communication |
| LoRa Module (Hub) | EBYTE E22-900T22D | 1 | Raspberry Pi gateway |
| Central Unit | Raspberry Pi 4 (4 GB) | 1 | Backend + gateway |
| Soil Moisture Sensor | Capacitive (3.3V) | 1 | Soil moisture measurement |
| Relay Module | 5V Single-channel Optocoupler | 1 | Pump switching |
| Li-ion Battery | 18650 3.7V ~3000 mAh | 2 | Edge power supply |
| Battery Holder | 2×18650 Series | 1 | 7.4V nominal output |

---

### Installation

#### Prerequisites

- Raspberry Pi 4 (Raspberry Pi OS Lite recommended)
- Python 3.10+
- PostgreSQL 14+
- Mosquitto MQTT Broker
- Arduino IDE (for ESP32 firmware)

#### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/AlperTimucinAkyol/akilli-sulama-sistemi.git
cd akilli-sulama-sistemi/backend

# 2. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database URL, JWT secret, OpenWeather API key

# 5. Start the backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

For ESP32 firmware, open `firmware/esp32_lora/esp32_lora.ino` in Arduino IDE, install the `LoRa_E22` library, set your `NODE_ID`, and upload to the board.

---

### Usage

- **Dashboard:** Navigate to `http://<raspberry-pi-ip>:8000`
- **API Docs:** Navigate to `http://<raspberry-pi-ip>:8000/docs`
- **Automatic Mode:** System makes irrigation decisions autonomously based on sensor + weather data
- **Manual Override:** Send direct pump commands from the dashboard
- **Custom Rules:** Define per-field irrigation rules (moisture threshold, temperature limit, rain block) from the field detail page

---

## 📁 Proje Yapısı / Project Structure

```
akilli-sulama-sistemi/
├── backend/
│   ├── api/
│   │   └── endpoints/          # auth, fields, irrigation, nodes, users, weather
│   ├── models/                 # SQLAlchemy ORM modelleri
│   ├── schemas/                # Pydantic şemaları
│   ├── services/
│   │   └── weather_service.py  # OpenWeather API entegrasyonu
│   ├── templates/              # Jinja2 HTML şablonları
│   ├── static/                 # CSS ve görseller
│   ├── main.py                 # FastAPI uygulama giriş noktası
│   ├── decision.py             # Sulama karar motoru
│   ├── lora_service.py         # LoRa Gateway servisi
│   ├── mqtt_client.py          # MQTT istemcisi
│   ├── offline_queue.py        # SQLite çevrimdışı kuyruk
│   ├── sync_worker.py          # Offline→PostgreSQL sync
│   ├── auth_utils.py           # JWT yardımcı fonksiyonlar
│   ├── database.py             # PostgreSQL bağlantı havuzu
│   └── requirements.txt
├── firmware/
│   └── esp32_lora/
│       └── esp32_lora.ino      # ESP32 Arduino firmware
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🛠️ Teknoloji Yığını / Tech Stack

| Katman / Layer | Teknoloji / Technology |
|----------------|------------------------|
| Edge MCU | ESP32 (Arduino/C++) |
| Wireless | LoRa E22-900T22D (SX1262) |
| Messaging | MQTT (Mosquitto) |
| Backend | FastAPI + Uvicorn (Python) |
| Database | PostgreSQL + SQLAlchemy ORM |
| Offline Queue | SQLite |
| Frontend | Jinja2 + HTML/CSS |
| Auth | JWT (HS256) + bcrypt |
| Weather | OpenWeather API |
| Power | 2× 18650 Li-ion (7.4V) |

---

## 📄 Lisans / License

Bu proje [MIT Lisansı](LICENSE) kapsamında lisanslanmıştır.  
This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

*Karadeniz Teknik Üniversitesi · Of Teknoloji Fakültesi · Yazılım Mühendisliği · 2026*

</div>
