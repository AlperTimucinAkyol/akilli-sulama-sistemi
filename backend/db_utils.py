from datetime import datetime
from sqlalchemy.orm import Session
import models

def save_sensor_data(lora_id: int, moisture_value: float, db: Session):
    node = db.query(models.Node).filter(models.Node.lora_id == lora_id).first()
    if not node:
        print(f"Hata: {lora_id} ID'li cihaz veritabanında kayıtlı değil!")
        return None, None

    sensor = db.query(models.Sensor).filter(
        models.Sensor.node_id == node.id,
        models.Sensor.sensor_type == "Soil Moisture"
    ).first()

    if not sensor:
        print(f"Bilgi: {lora_id} için 'Soil Moisture' sensörü oluşturuluyor...")
        sensor = models.Sensor(node_id=node.id, sensor_type="Soil Moisture", created_at=datetime.now())
        db.add(sensor)
        db.commit()
        db.refresh(sensor)

    new_data = models.SensorData(sensor_id=sensor.id, value=float(moisture_value), timestamp=datetime.now())
    db.add(new_data)
    node.last_seen = datetime.now()
    db.commit()

    return node

def get_field_location(field_id: int, db: Session):
    field = db.query(models.Field).filter(models.Field.id == field_id).first()
    return field.location if field and field.location else "Istanbul"