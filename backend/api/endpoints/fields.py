from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.users import User
from models.fields import Field
from models.iot import Node, Sensor, SensorData 
from datetime import datetime, timedelta
from schemas.field_schemas import *
import auth_utils

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    total_fields = db.query(Field).filter(Field.user_id == current_user.id).count()

    fields_data = []
    user_fields = db.query(Field).filter(Field.user_id == current_user.id).all()

    for field in user_fields:
        latest_moisture = db.query(SensorData.value)\
            .join(Sensor).join(Node)\
            .filter(Node.field_id == field.id, Sensor.sensor_type == 'soil_moisture')\
            .order_by(SensorData.timestamp.desc()).first()

        fields_data.append({
            "id": field.id,
            "name": field.name,
            "location": f"{field.location}",
            "last_moisture": latest_moisture[0] if latest_moisture else "N/A",
            "status": "Online"
        })

    return {
        "total_fields": total_fields,
        "fields": fields_data
    }
    
@router.get("/moisture-comparison")
async def get_comparison_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    user_fields = db.query(Field).filter(Field.user_id == current_user.id).all()
    labels = []
    values = []

    for field in user_fields:
        latest = db.query(SensorData.value)\
            .join(Sensor).join(Node)\
            .filter(Node.field_id == field.id, Sensor.sensor_type == 'soil_moisture')\
            .order_by(SensorData.timestamp.desc()).first()
        
        labels.append(field.name)
        values.append(latest[0] if latest else 0)

    return {"labels": labels, "values": values}

@router.get("/{field_id}/detail", response_model=FieldDetailResponse)
async def get_field_detail(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")

    nodes = db.query(Node).filter(Node.field_id == field_id).all()
    
    nodes_data = []
    for node in nodes:
        sensors = db.query(Sensor).filter(Sensor.node_id == node.id).all()
        sensor_list = []
        for s in sensors:
            last_val = db.query(SensorData).filter(SensorData.sensor_id == s.id)\
                         .order_by(SensorData.timestamp.desc()).first()
            sensor_list.append({
                "type": s.sensor_type,
                "value": str(last_val.value) if last_val else "N/A"
            })
            
        nodes_data.append({
            "node_id": node.id, 
            "lora_id": node.lora_id, 
            "status": node.status,      
            "last_seen": node.last_seen,
            "sensors": sensor_list
        })

    return {
        "field_name": field.name,
        "location": field.location,
        "nodes": nodes_data
    }

@router.get("/{field_id}/history")
async def get_field_history(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")

    time_threshold = datetime.now() - timedelta(hours=24)

    history = db.query(SensorData.value, SensorData.timestamp)\
        .join(Sensor).join(Node)\
        .filter(
            Node.field_id == field_id,
            Sensor.sensor_type == 'soil_moisture',
            SensorData.timestamp >= time_threshold
        )\
        .order_by(SensorData.timestamp.asc()).all()

    labels = [data.timestamp.strftime("%H:%M") for data in history]
    values = [data.value for data in history]

    return {"labels": labels, "values": values}

@router.get("/", response_model=list[FieldResponse])
async def get_fields(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    fields = db.query(Field).filter(Field.user_id == current_user.id).all()
    return fields

@router.post("/add", response_model=FieldResponse)
async def add_field(
    field_data: FieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    new_field = Field(**field_data.model_dump(), user_id=current_user.id)
    
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    
    return new_field

@router.delete("/{field_id}")
async def delete_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")
        
    db.delete(field)
    db.commit()
    return {"message": "Tarla başarıyla silindi"}

@router.put("/{field_id}")
async def update_field(
    field_id: int,
    update_data: FieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(field, key, value)
    
    db.commit()
    return {"message": "Tarla başarıyla güncellendi"}