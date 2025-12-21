from machine import ADC, Pin
import time

from config import NEM_ESIK_ADC, OKUMA_ARALIGI_S

adc = ADC(Pin(34))           
pump_relay = Pin(25, Pin.OUT) 
adc.atten(ADC.ATTN_11DB)     

def oku_nem():
    return adc.read()

def sulama_kontrol(nem_degeri):
    if nem_degeri > NEM_ESIK_ADC:
        pump_relay.on()
        return True
    else:
        pump_relay.off()
        return False


print("Akıllı Sulama Sistemi Başlatıldı")
while True:
    nem = oku_nem()
    sulama = sulama_kontrol(nem)
    durum = "ASIYOR" if sulama else "YETERLI"
    print(f"[{time.ticks_ms() // 1000}] Nem: {nem} → {durum}")
    time.sleep(OKUMA_ARALIGI_S)