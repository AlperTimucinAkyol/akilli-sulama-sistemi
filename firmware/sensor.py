from machine import Pin, ADC
import time

class SensorManager:
    def __init__(self, moisture_pin=34):
        self.moisture_adc = ADC(Pin(moisture_pin))
        
        # 0V - 3.3V aralığında okuma yapabilmek için attenüasyon ayarı
        # Bu ayar olmadan 1.1V üzerini okuyamazsın.
        self.moisture_adc.atten(ADC.ATTN_11DB) 
        
        # --- KALİBRASYON DEĞERLERİ ---
        self.dry_value = 3200  # örnek bir değer
        self.wet_value = 1200  # örnek bir değer

    def get_data(self):
        try:
            raw_val = self.moisture_adc.read()
            
            # Formül: ((Kuru - Mevcut) / (Kuru - Islak)) * 100
            percentage = ((self.dry_value - raw_val) / (self.dry_value - self.wet_value)) * 100
            
            # konfigürasyon 0 ile 100 arasında sınırla
            moisture_pct = max(0, min(100, round(percentage, 2)))
            
            return {
                "soil_moisture": moisture_pct,
                "raw_value": raw_val
            }
        except Exception as e:
            print("Sensör okuma hatası:", e)
            return None