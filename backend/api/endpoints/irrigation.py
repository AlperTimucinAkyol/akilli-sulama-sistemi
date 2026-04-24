from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.users import User
from models.fields import Field
from models.iot import Node, IrrigationLog
from schemas.irrigation_schemas import IrrigationLogResponse
import auth_utils
from models.iot import IrrigationRule
from schemas.irrigation_rule_schemas import IrrigationRuleCreate


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


@router.post("/rules")
async def create_rule(
    rule_in: IrrigationRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_utils.get_current_user)
):
    # Tarlaya ait mevcut kuralı bul
    existing_rule = db.query(IrrigationRule).filter(
        IrrigationRule.field_id == rule_in.field_id
    ).first()

    if existing_rule:
        raise HTTPException(
            status_code=400, 
            detail="Bu tarlanın zaten bir kuralı var. Lütfen mevcut kuralı güncelleyin."
        )
    
    # Create Logic: Kural yoksa yeni oluştur
    new_rule = IrrigationRule(**rule_in.model_dump())
    db.add(new_rule)
    db.commit()
    return {"status": "created", "id": new_rule.id}

@router.get("/rules/field/{field_id}")
async def get_field_rule(
    field_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(auth_utils.get_current_user)
):
    # Tarlanın kullanıcıya ait olup olmadığını da kontrol ederek kuralı çekiyoruz
    rule = db.query(IrrigationRule).filter(
        IrrigationRule.field_id == field_id
    ).first()

    if not rule:
        # Eğer kural yoksa 404 döneriz, JS bunu "Ekleme Modu" olarak algılar
        raise HTTPException(status_code=404, detail="Bu tarla için kural bulunamadı.")

    return rule

@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule_in: IrrigationRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth_utils.get_current_user)
):
    # 1. Güncellenecek kuralı ID ile bul
    db_rule = db.query(IrrigationRule).filter(IrrigationRule.id == rule_id).first()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="Güncellenecek kural bulunamadı.")

    # 2. Gelen verileri mevcut kuralın üzerine yaz (Update)
    update_data = rule_in.model_dump()
    for key, value in update_data.items():
        setattr(db_rule, key, value)

    db.commit()
    db.refresh(db_rule)
    
    return {"status": "updated", "id": db_rule.id}