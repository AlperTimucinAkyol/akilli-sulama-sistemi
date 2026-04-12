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
    lora_id: str = Form(...), # cihazın kimliği
    db: Session = Depends(get_db),
    current_user = Depends(auth_utils.get_current_user)
):
    field = db.query(Field).filter(Field.id == field_id, Field.user_id == current_user.id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")
    
    existing_node = db.query(Node).filter(Node.lora_id == lora_id).first()
    if existing_node:
        raise HTTPException(status_code=400, detail="Bu LoRa ID zaten sisteme kayıtlı.")

    try:
        new_node = Node(
            field_id=field_id,
            lora_id=lora_id,
            status="Offline" # İlk eklendiğinde offline başlar
        )
        db.add(new_node)
        db.flush()

        new_sensor = Sensor(
            node_id=new_node.id,
            sensor_type="soil_moisture"
        )
        db.add(new_sensor)
        
        db.commit()
        return {"message": f"{lora_id} kimlikli cihaz ve sensör başarıyla tanımlandı."}

    except Exception as e:
        db.rollback()
        print(f"Hata: {e}")
        raise HTTPException(status_code=500, detail="Cihaz eklenirken bir veritabanı hatası oluştu.")