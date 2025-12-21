# Akıllı Sulama Sistemi

TÜBİTAK 2209-A Projesi – Karadeniz Teknik Üniversitesi  
Alper Timuçin Akyol, Erdinç Topuz  
Danışman: Arş. Gör. Betül MUMCU

## 🧪 Wokwi Simülasyonu
[Wokwi'de simülasyonu denemek için tıklayın](https://wokwi.com/projects/450944928406436865)  


## Dizin Yapısı
- `firmware/` → ESP32 MicroPython kodları
- `wokwi/` → Tarayıcıda simülasyon için
- `docs/` → Kalibrasyon ve sistem dokümantasyonu

## 📄 Lisans
MIT

## Proje Hedefleri
- Bağlantı şeması tanımlı, ancak LoRa henüz kodlanmadı.
- Sadece sensör okuma + temel karar mekanizması hazır. LoRa ve MQTT entegrasyonu eksik.
- Gateway henüz yapılandırılmadı.
- Backend-> OpenWeather API, EPİAŞ API, Karar motoru, Veri tabanı + REST API: henüz başlatılmadı.
- Web Arayüzü: henüz başlatılmadı.
- Saha Testi: Henüz mümkün değil.

## Mevcut Durum
### Ne çalışıyor?
- ESP32, CSMS sensörünü okuyor (GPIO34)
- Kullanıcı tanımlı bir eşik değere göre sulama kararı veriyor.
- Pompa/röle(LED) sinyali veriliyor (GPIO25).
- Wokwi’de potansiyometreyle simüle edilebiliyor.
