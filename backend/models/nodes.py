from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

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
    # irrigation_logs = relationship("IrrigationLog", back_populates="node")