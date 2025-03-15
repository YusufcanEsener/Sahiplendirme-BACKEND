from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId

class UserBase(BaseModel):
    """Temel kullanıcı modeli"""
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_admin: bool = False

class UserCreate(UserBase):
    """Kullanıcı oluşturma modeli - şifre içerir"""
    password: str

class UserInDB(UserBase):
    """Veritabanında saklanan kullanıcı modeli"""
    password_hash: str

class UserResponse(UserBase):
    """API yanıtlarında kullanılan kullanıcı modeli - şifre içermez"""
    id: str
    
    class Config:
        from_attributes = True

# MongoDB için kullanıcı belge şeması
user_schema = {
    "first_name": {"type": "string", "required": True},
    "last_name": {"type": "string", "required": True},
    "email": {"type": "string", "required": True, "unique": True},
    "password_hash": {"type": "string", "required": True},
    "phone": {"type": "string", "required": False},
    "is_admin": {"type": "boolean", "default": False}
}

# Şifre işlemleri için yardımcı fonksiyonlar
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Düz metin şifreyi hash ile karşılaştırır"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Şifreyi güvenli bir şekilde hashler"""
    return pwd_context.hash(password)
