from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserResponse, get_password_hash, verify_password
from app.db.database import users_collection, parse_json
from bson import ObjectId
from datetime import datetime, timedelta

from typing import Optional
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token,authenticate_user


router = APIRouter()
# Token oluşturma fonksiyonu

# Kayıt olma endpoint'i
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    # Email adresinin benzersiz olduğunu kontrol et
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kullanılıyor"
        )
    
    # Kullanıcı verisini hazırla
    user_data = user.dict()
    
    # Şifreyi hashle
    password = user_data.pop("password")
    user_data["password_hash"] = get_password_hash(password)
    
    # Varsayılan değerleri ayarla
    if "is_admin" not in user_data:
        user_data["is_admin"] = False
    
    # MongoDB'ye ekle
    result = users_collection.insert_one(user_data)
    
    # Oluşturulan kullanıcıyı döndür
    created_user = users_collection.find_one({"_id": result.inserted_id})
    created_user["id"] = str(created_user["_id"])
    
    return parse_json(created_user)

# Giriş yapma endpoint'i
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı email veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Mevcut kullanıcı bilgilerini alma
