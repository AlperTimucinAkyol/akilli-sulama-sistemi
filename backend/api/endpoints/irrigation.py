from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.users import User
from models.fields import Field
from models.iot import Node, IrrigationLog
from schemas.irrigation_schemas import IrrigationLogResponse
import auth_utils


router = APIRouter()


@router.get("/logs", response_model=list[IrrigationLogResponse])
async def get_irrigation_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    
    logs = db.query(
        IrrigationLog, 
        Field.name.label("field_name"), 
        Node.lora_id.label("lora_id")
    ).join(Field, IrrigationLog.field_id == Field.id)\
     .join(Node, IrrigationLog.node_id == Node.id)\
     .filter(Field.user_id == current_user.id)\
     .order_by(IrrigationLog.timestamp.desc()).all()

    return [
        {
            **log.__dict__, 
            "field_name": field_name, 
            "lora_id": lora_id
        } for log, field_name, lora_id in logs
    ]