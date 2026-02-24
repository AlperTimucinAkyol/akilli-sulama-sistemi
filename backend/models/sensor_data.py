from sqlalchemy import Column, Integer, String, Date, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    value = Column(Float) # Ölçülen değer --> nem
    timestamp = Column(DateTime) 

    # İlişkiler
    sensor = relationship("Sensor", back_populates="data_points")