from pymongo import MongoClient
from fastapi import FastAPI
from app.api.routes import router

client = MongoClient("mongodb://localhost:27017/")
db = client["sahiplendirme"]
ilanlar_collection = db["ilanlar"]

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Sahiplendirme API'ye Hoş Geldiniz!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
