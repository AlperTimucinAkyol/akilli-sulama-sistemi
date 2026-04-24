from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"))
    lora_id = Column(String(255), nullable=False)
    status = Column(String(255))
    last_seen = Column(String(255)) # timestamp olabilir
    created_at = Column(Date)

    # İlişkiler
    field = relationship("Field", back_populates="nodes")
    sensors = relationship("Sensor", back_populates="node")
    irrigation_logs = relationship("IrrigationLog", back_populates="node")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("nodes.id"))
    sensor_type = Column(String(255))
    created_at = Column(Date)

    # İlişkiler
    node = relationship("Node", back_populates="sensors")
    data_points = relationship("SensorData", back_populates="sensor")
    
    
class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    value = Column(Float) # Ölçülen değer --> nem
    timestamp = Column(DateTime) 

    # İlişkiler
    sensor = relationship("Sensor", back_populates="data_points")
    

class IrrigationLog(Base):
    __tablename__ = "irrigation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"))
    node_id = Column(Integer, ForeignKey("nodes.id"))
    action = Column(Boolean) # True: Başlatıldı, False: Durduruldu
    mode = Column(Boolean)   # True: Otomatik, False: Manuel
    duration_min = Column(Float)
    soil_moisture = Column(Float)
    decision_note = Column(String)
    timestamp = Column(DateTime, default=datetime.now)

    field = relationship("Field", back_populates="irrigation_logs")
    node = relationship("Node", back_populates="irrigation_logs")
    

class IrrigationRule(Base):
    __tablename__ = "irrigation_rules"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"))
    name = Column(String(100))
    min_soil_moisture = Column(Float)
    max_temperature = Column(Float)
    duration_min = Column(Integer)
    rain_block = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())