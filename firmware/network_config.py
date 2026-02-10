import network
import time
from config import SSID, PASSWORD

def wifi_baglan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False) 
    time.sleep(1)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("WiFi'a bağlanılıyor...", end="")
    timeout = 0
    while not wlan.isconnected() and timeout < 10:
        print(".", end="")
        time.sleep(1)
        timeout += 1
        
    if wlan.isconnected():
        print("\nBağlandı! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("\nBağlanamadı!")
        return False
