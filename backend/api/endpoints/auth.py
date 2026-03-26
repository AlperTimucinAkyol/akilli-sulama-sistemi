from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User
import auth_utils

router = APIRouter()

@router.post("/register")
async def register(
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    new_user = User(
        first_name=firstName,
        last_name=lastName,
        email=email,
        hashed_password=auth_utils.hash_password(password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Kayıt başarıyla tamamlandı!", "user_id": new_user.id}