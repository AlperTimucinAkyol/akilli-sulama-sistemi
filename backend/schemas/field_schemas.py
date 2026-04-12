from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class FieldBase(BaseModel):
    name: str
    location: str
    area_m2: float
    crop_type: str
    
class FieldCreate(FieldBase):
    pass

class FieldUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    area_m2: Optional[float] = None
    crop_type: Optional[str] = None
    
class FieldResponse(FieldBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Dashboard özeti için DTO
class DashboardSummary(BaseModel):
    total_fields: int
    fields: List[dict]

# Detay sayfası için sensör verisi DTO
class SensorDetail(BaseModel):
    type: str
    value: str

# Detay sayfası için Node DTO
class NodeDetail(BaseModel):
    node_id: int
    lora_id: str
    status: str
    last_seen: Optional[datetime] = None
    sensors: List[SensorDetail]

# Tarla detay sayfası DTO
class FieldDetailResponse(BaseModel):
    field_name: str
    location: str
    nodes: List[NodeDetail]