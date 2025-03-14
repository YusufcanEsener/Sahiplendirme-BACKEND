from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import sys
from bson import ObjectId
import json

# MongoDB bağlantı bilgileri
MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "sahiplendirme"
COLLECTION_NAME = "ilanlar"
COUNTER_COLLECTION_NAME = "counters"

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def parse_json(data):
    """MongoDB sonuçlarını JSON uyumlu formata dönüştürür"""
    return json.loads(json.dumps(data, cls=JSONEncoder))

try:
    # MongoDB sunucusuna bağlantı kurma
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    
    # Bağlantıyı test etme
    client.admin.command('ping')
    
    print("MongoDB bağlantısı başarıyla kuruldu!")
    print(f"Veritabanı: {DB_NAME}")
    print(f"Koleksiyon: {COLLECTION_NAME}")
    
    # Veritabanı ve koleksiyonu tanımlama
    db = client[DB_NAME]
    ilanlar_collection = db[COLLECTION_NAME]
    counters_collection = db[COUNTER_COLLECTION_NAME]
    
    # Mevcut indeksleri kontrol et ve temizle
    try:
        ilanlar_collection.drop_index("ilan_no_1")
        print("Mevcut indeks temizlendi.")
    except Exception:
        print("Mevcut indeks bulunamadı.")
    
    # Mevcut verileri kontrol et ve düzenle
    # İlan_no değeri olmayan belgeler için ilan_no ekle
    bulk_ops = []
    existing_ilan_nos = set()
    highest_ilan_no = 0

    for ilan in ilanlar_collection.find():
        if "ilan_no" in ilan:
            existing_ilan_nos.add(ilan["ilan_no"])
            highest_ilan_no = max(highest_ilan_no, ilan["ilan_no"])
        else:
            # ilan_no olmayan belgelere geçici ilan_no ata (ileride güncellenecek)
            ilanlar_collection.update_one({"_id": ilan["_id"]}, {"$set": {"ilan_no": -1}})

    # Tekrarlanan ilan_no'ları çöz
    duplicates = ilanlar_collection.aggregate([
        {"$group": {"_id": "$ilan_no", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ])
    
    for dup in duplicates:
        # Tekrarlanan ilan_no'ya sahip belgeleri bul
        duplicate_ilans = list(ilanlar_collection.find({"ilan_no": dup["_id"]}))
        
        # İlk belgeyi atla, diğerlerine yeni ilan_no değerleri ata
        for i in range(1, len(duplicate_ilans)):
            highest_ilan_no += 1
            ilanlar_collection.update_one(
                {"_id": duplicate_ilans[i]["_id"]}, 
                {"$set": {"ilan_no": highest_ilan_no}}
            )
    
    # Sayaç koleksiyonunu oluştur veya güncelle
    if not counters_collection.find_one({"_id": "ilan_id"}):
        counters_collection.insert_one({"_id": "ilan_id", "seq": highest_ilan_no})
    else:
        counters_collection.update_one(
            {"_id": "ilan_id"}, 
            {"$set": {"seq": highest_ilan_no}}
        )
    
    # Şimdi unique indeksi oluştur
    print("Yeni unique indeks oluşturuluyor...")
    ilanlar_collection.create_index("ilan_no", unique=True)
    print("Unique indeks başarıyla oluşturuldu.")
    
except ConnectionFailure as e:
    print(f"MongoDB bağlantısı kurulamadı: {e}", file=sys.stderr)
    sys.exit(1)
except DuplicateKeyError as e:
    print(f"Duplicate key hatası: {e}", file=sys.stderr)
    print("Mevcut ilan_no değerlerinde çakışma var, veritabanı temizlenmeli.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Beklenmeyen bir hata oluştu: {e}", file=sys.stderr)
    sys.exit(1)

def get_next_sequence_value(sequence_name):
    """Belirtilen sıra için bir sonraki değeri alır ve günceller"""
    # Önce sayaç belgesinin var olup olmadığını kontrol et
    counter = counters_collection.find_one({"_id": sequence_name})
    
    if counter is None:
        # Sayaç belgesi yoksa oluştur
        print(f"Sayaç belgesi '{sequence_name}' bulunamadı, yeni oluşturuluyor...")
        # Mevcut en yüksek ilan_no'yu bul
        highest_ilan_no = 0
        if ilanlar_collection.count_documents({}) > 0:
            highest_doc = ilanlar_collection.find_one(
                {}, 
                sort=[("ilan_no", -1)]
            )
            if highest_doc and "ilan_no" in highest_doc:
                highest_ilan_no = highest_doc["ilan_no"]
        
        # Yeni sayaç belgesi oluştur
        counters_collection.insert_one({"_id": sequence_name, "seq": highest_ilan_no})
        
    # Sayaç değerini arttır ve yeni değeri al
    sequence_document = counters_collection.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        return_document=True
    )
    
    # Hala None ise, ciddi bir sorun var
    if sequence_document is None:
        print(f"HATA: Sayaç belgesi '{sequence_name}' güncellenemedi!", file=sys.stderr)
        # Acil durum çözümü: Rastgele büyük bir sayı döndür
        import time
        return int(time.time())
    
    return sequence_document["seq"]

def check_connection():
    """MongoDB bağlantısını yeniden kontrol eden fonksiyon"""
    try:
        client.admin.command('ping')
        return True, "MongoDB bağlantısı aktif"
    except Exception as e:
        return False, f"MongoDB bağlantısı hatalı: {e}"
