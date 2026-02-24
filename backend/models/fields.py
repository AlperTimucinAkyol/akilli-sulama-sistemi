from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255))
    location = Column(String(255))
    area_m2 = Column(String(255))
    crop_type = Column(String(255))
    created_at = Column(Date)

    # İlişkiler
    owner = relationship("User", back_populates="fields")
    nodes = relationship("Node", back_populates="field")
    # irrigation_rules = relationship("IrrigationRule", back_populates="field")
    # irrigation_logs = relationship("IrrigationLog", back_populates="field")