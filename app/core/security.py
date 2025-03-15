from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, Request
from jose import jwt, JWTError
from app.db.database import users_collection, parse_json
from app.models.user import verify_password
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter,status


# JWT ayarları
SECRET_KEY = "sahiplendirme_gizli_anahtar_degistirin"  # Gerçek uygulamada güvenli bir şekilde saklayın
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 şeması
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Kullanıcı doğrulama fonksiyonu
def authenticate_user(email: str, password: str):
    user = users_collection.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

# Token doğrulama ve mevcut kullanıcıyı alma
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz kimlik bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    user["id"] = str(user["_id"])
    return parse_json(user)

# Yönetici kullanıcı kontrolü
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkileri gerekiyor"
        )
    return current_user

# İlan işlemleri için yetki kontrolü
async def check_ilan_permission(request: Request, current_user: dict = Depends(get_current_user)):
    # Admin kullanıcılar tüm işlemleri yapabilir
    if current_user.get("is_admin"):
        return current_user
    
    # Normal kullanıcılar sadece GET isteklerini yapabilir
    if request.method != "GET":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkileri gerekiyor. Normal kullanıcılar sadece ilanları görüntüleyebilir."
        )
    
    return current_user
