from sqlalchemy import Column, Integer, String, Date, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("nodes.id"))
    sensor_type = Column(String(255))
    created_at = Column(Date)

    # İlişkiler
    node = relationship("Node", back_populates="sensors")
    data_points = relationship("SensorData", back_populates="sensor")