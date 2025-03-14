# app/models.py
from pydantic import BaseModel
from typing import Optional

class Ilan(BaseModel):
    ilan_no: int
    tur: str
    cins: str
    yas: str
    cinsiyet: str
    saglik_durumu: str
    karakter_ozellikleri: str
    bulundugu_yer: str
    iletisim: str
    hikaye: str

class IlanCreate(BaseModel):
    tur: str
    cins: str
    yas: str
    cinsiyet: str
    saglik_durumu: str
    karakter_ozellikleri: str
    bulundugu_yer: str
    iletisim: str
    hikaye: str

class IlanResponse(BaseModel):
    ilan_no: int
    tur: str
    cins: str
    yas: str
    cinsiyet: str
    saglik_durumu: str
    karakter_ozellikleri: str
    bulundugu_yer: str
    iletisim: str
    hikaye: str
    
    class Config:
        orm_mode = True