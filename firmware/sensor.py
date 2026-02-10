import dht
from machine import Pin

class SensorManager:
    def __init__(self, pin_no):
        self.sensor = dht.DHT11(Pin(pin_no))
    
    def get_data(self):
        try:
            self.sensor.measure()
            return {
                "temperature": float(self.sensor.temperature()),
                "humidity": float(self.sensor.humidity())
            }
        except Exception as e:
            print("Sensör okunamadı:", e)
            return None
