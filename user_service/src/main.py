from fastapi import FastAPI, HTTPException, Request
from .database import UserDatabase
from pydantic import BaseModel
import os

app = FastAPI(title="User Service (YazLab2)")
db = UserDatabase()

DISPATCHER_SECRET = "proje_ozel_anahtar_123"

class UserSchema(BaseModel):
    name: str
    email: str

# --- HEALTH CHECK ---
# Dispatcher veya Prometheus'un servisin ayakta olduğunu anlaması için
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "user_service"}

# İstek: GET http://user_service:8001/{user_id}
@app.get("/{user_id}")
async def get_user(user_id: str, request: Request):
    # Dispatcher anahtarı kontrolü
    if request.headers.get("x-dispatcher-key") != DISPATCHER_SECRET:
        raise HTTPException(status_code=401, detail="Yetkisiz Erişim: Dispatcher anahtarı hatalı")
    
    user_data = db.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # MongoDB _id nesnesini string'e çeviriyoruz
    user_data["_id"] = str(user_data["_id"])
    return user_data

# --- ADD USER ---

@app.post("/", status_code=201)
async def add_user(user: UserSchema, request: Request):
    # Dispatcher anahtarı kontrolü
    if request.headers.get("x-dispatcher-key") != DISPATCHER_SECRET:
        raise HTTPException(status_code=401, detail="Yetkisiz Erişim")
    
    try:
        user_id = db.create_user(user.dict())
        return {
            "status": "success",
            "id": str(user_id), 
            "message": "Kullanıcı başarıyla oluşturuldu"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Tüm kullanıcıları listeleme
@app.get("/")
async def get_all_users(request: Request):
    if request.headers.get("x-dispatcher-key") != DISPATCHER_SECRET:
        raise HTTPException(status_code=401, detail="Yetkisiz Erişim")
    
    return {"message": "Tüm kullanıcıları listeleme endpoint'i aktif"}