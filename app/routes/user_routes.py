from fastapi import APIRouter, HTTPException, Depends, status
from app.models.user import UserCreate, UserResponse, get_password_hash, verify_password
from app.db.database import users_collection, parse_json
from bson import ObjectId

router = APIRouter()

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
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

@router.get("/users/", response_model=list[UserResponse])
async def get_users():
    users = list(users_collection.find())
    for user in users:
        user["id"] = str(user["_id"])
    
    return parse_json(users)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz kullanıcı ID formatı"
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    user["id"] = str(user["_id"])
    return parse_json(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserCreate):
    # Kullanıcının var olup olmadığını kontrol et
    try:
        existing_user = users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz kullanıcı ID formatı"
        )
    
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Email değişiyorsa, yeni email'in benzersiz olduğunu kontrol et
    if user_update.email != existing_user["email"]:
        if users_collection.find_one({"email": user_update.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kullanılıyor"
            )
    
    # Kullanıcı verisini hazırla
    user_data = user_update.dict()
    
    # Şifreyi hashle
    password = user_data.pop("password")
    user_data["password_hash"] = get_password_hash(password)
    
    # MongoDB'de güncelle
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_data}
    )
    
    # Güncellenmiş kullanıcıyı döndür
    updated_user = users_collection.find_one({"_id": ObjectId(user_id)})
    updated_user["id"] = str(updated_user["_id"])
    
    return parse_json(updated_user)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    try:
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz kullanıcı ID formatı"
        )
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    return None 