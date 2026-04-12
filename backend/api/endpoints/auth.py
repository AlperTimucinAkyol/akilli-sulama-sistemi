from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User
from datetime import datetime, timezone, timedelta
import re
import auth_utils
from fastapi.security import OAuth2PasswordRequestForm
from config import Config

router = APIRouter()

@router.post("/register")
async def register(
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="Geçersiz e-posta formatı.")

    password_error = auth_utils.validate_password(password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)
    
    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    new_user = User(
        first_name=firstName,
        last_name=lastName,
        email=email,
        password_hash=auth_utils.hash_password(password),
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Kayıt başarıyla tamamlandı!", "user_id": new_user.id}

@router.post("/login")
async def login(
    email: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not auth_utils.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id
            }, 
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "first_name": user.first_name,
        "message": "Giriş başarılı!",
    }