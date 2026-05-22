from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from models.iot import Node, Sensor
from models.fields import Field
import auth_utils

router = APIRouter()

@router.post("/add")
async def add_node(
    field_id: int = Form(...),
    lora_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")
    
    existing = db.query(Node).filter(Node.lora_id == lora_id, Node.field_id == field_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu isimde bir cihaz zaten bu tarlaya kayıtlı.")

    try:
        new_node = Node(
            field_id=field_id,
            lora_id=lora_id,
            status="Online" # İlk eklendiğinde offline başlar
        )
        db.add(new_node)
        db.flush()

        new_sensor = Sensor(
            node_id=new_node.id,
            sensor_type="soil_moisture"
        )
        db.add(new_sensor)
        
        db.commit()
        return {"message": f"'{lora_id}' cihazı ve toprak nemi sensörü başarıyla eklendi."}

    except Exception as e:
        db.rollback()
        print(f"Hata: {e}")
        raise HTTPException(status_code=500, detail="Cihaz eklenirken bir veritabanı hatası oluştu.")
