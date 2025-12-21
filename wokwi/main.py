from machine import ADC, Pin
import time

adc = ADC(Pin(34))
pump = Pin(25, Pin.OUT)
adc.atten(ADC.ATTN_11DB)

NEM_ESIK = 2000

def kontrol():
    nem = adc.read()
    print(f"Nem ADC: {nem}")
    if nem > NEM_ESIK:
        print("→ Sulama BAŞLATILIYOR")
        pump.on()
    else:
        print("→ Sulama GEREKSİZ")
        pump.off()

print("Wokwi Simülasyonu Başladı")
while True:
    kontrol()
    time.sleep(5)