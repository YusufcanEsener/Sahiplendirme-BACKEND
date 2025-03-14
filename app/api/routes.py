from fastapi import APIRouter, HTTPException
from app.models.models import Ilan, IlanCreate, IlanResponse
from app.db.database import ilanlar_collection, parse_json, get_next_sequence_value

router = APIRouter()

@router.post("/ilanlar/", response_model=IlanResponse)
async def create_ilan(ilan: IlanCreate):
    # Otomatik olarak bir sonraki ilan_no'yu al
    next_ilan_no = get_next_sequence_value("ilan_id")
    
    # Gelen verileri dict'e çevir ve ilan_no ekle
    ilan_dict = ilan.dict()
    ilan_dict["ilan_no"] = next_ilan_no
    
    # MongoDB'ye ekle
    result = ilanlar_collection.insert_one(ilan_dict)
    
    # Oluşturulan ilanı döndür
    created_ilan = ilanlar_collection.find_one({"_id": result.inserted_id})
    return parse_json(created_ilan)

@router.get("/ilanlar/", response_model=list[IlanResponse])
async def get_ilanlar():
    # Tüm sonuçları JSON uyumlu formata dönüştür
    ilanlar = list(ilanlar_collection.find())
    return parse_json(ilanlar)

@router.get("/ilanlar/{ilan_no}", response_model=IlanResponse)
async def get_ilan(ilan_no: int):
    ilan = ilanlar_collection.find_one({"ilan_no": ilan_no})
    if ilan is None:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")
    # İlanı JSON uyumlu formata dönüştür
    return parse_json(ilan)

@router.put("/ilanlar/{ilan_no}", response_model=IlanResponse)
async def update_ilan(ilan_no: int, ilan: IlanCreate):
    # İlan numarasını değiştirmeye izin verme
    ilan_dict = ilan.dict()
    
    # İlan var mı kontrol et
    existing_ilan = ilanlar_collection.find_one({"ilan_no": ilan_no})
    if not existing_ilan:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")
    
    # Güncelle
    result = ilanlar_collection.update_one({"ilan_no": ilan_no}, {"$set": ilan_dict})
    
    # Güncellenmiş ilanı döndür
    updated_ilan = ilanlar_collection.find_one({"ilan_no": ilan_no})
    return parse_json(updated_ilan)

@router.delete("/ilanlar/{ilan_no}")
async def delete_ilan(ilan_no: int):
    result = ilanlar_collection.delete_one({"ilan_no": ilan_no})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")
    return {"message": "İlan silindi"}