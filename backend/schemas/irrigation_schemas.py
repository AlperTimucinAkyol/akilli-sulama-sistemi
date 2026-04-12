from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Base Model (Ortak Alanlar)
class IrrigationLogBase(BaseModel):
    action: bool
    mode: bool
    duration_min: float
    soil_moisture: float
    decision_note: Optional[str] = None


class IrrigationLogCreate(IrrigationLogBase):
    field_id: int
    node_id: int


class IrrigationLogResponse(IrrigationLogBase):
    id: int
    timestamp: datetime
    field_name: str 
    lora_id: str     

    model_config = ConfigDict(from_attributes=True)