from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
import auth_utils
from models.users import User

router = APIRouter()

@router.get("/me")
async def read_user_me(current_user: User = Depends(auth_utils.get_current_user)):
    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email
    }

@router.post("/update")
async def update_user(
    firstName: str = Form(...),
    lastName: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    current_user.first_name = firstName
    current_user.last_name = lastName
    
    db.commit()
    return {"message": "Profil başarıyla güncellendi!"}


@router.post("/update-password")
async def update_password(
    oldPassword: str = Form(...),
    newPassword: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_user)
):
    if not auth_utils.verify_password(oldPassword, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifreniz hatalı.")

    password_error = auth_utils.validate_password(newPassword)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    if oldPassword == newPassword:
        raise HTTPException(status_code=400, detail="Yeni şifre eskisiyle aynı olamaz.")

    current_user.password_hash = auth_utils.hash_password(newPassword)
    db.commit()

    return {"message": "Şifreniz başarıyla güncellendi!"}