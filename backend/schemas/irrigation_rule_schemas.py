from pydantic import BaseModel
from typing import Optional

class IrrigationRuleCreate(BaseModel):
    field_id: int
    name: str
    min_soil_moisture: float
    max_temperature: float
    duration_min: int  # Sulama süresi (Basit yapı için ekledik)
    rain_block: bool = True