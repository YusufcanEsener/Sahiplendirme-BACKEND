from pymongo import MongoClient
from fastapi import FastAPI
from app.api import routers,auth,users

client = MongoClient("mongodb://localhost:27017/")
db = client["sahiplendirme"]
ilanlar_collection = db["ilanlar"]

app = FastAPI()

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["Kullanıcılar"])
app.include_router(routers.router, prefix="/api/routes", tags=["İlanlar"])


@app.get("/")
async def root():
    return {"message": "Sahiplendirme API'ye Hoş Geldiniz!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
