from fastapi import FastAPI, HTTPException, Request
from .database import ProductDatabase
from pydantic import BaseModel

app = FastAPI(title="Product Service")
db = ProductDatabase()
DISPATCHER_SECRET = "proje_ozel_anahtar_123" # Dispatcher ile aynı olmalı [cite: 48]

class ProductSchema(BaseModel):
    name: str
    price: float

@app.get("/products/{product_id}")
async def get_product(product_id: str, request: Request):
    # Network Isolation: Sadece Dispatcher'dan gelen isteği kabul et [cite: 48, 49]
    if request.headers.get("x-dispatcher-key") != DISPATCHER_SECRET:
        raise HTTPException(status_code=401, detail="Yetkisiz Erişim")
    
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Urun bulunamadi")
    product["_id"] = str(product["_id"])
    return product

@app.post("/products", status_code=201)
async def add_product(product: ProductSchema, request: Request):
    if request.headers.get("x-dispatcher-key") != DISPATCHER_SECRET:
        raise HTTPException(status_code=401)
    
    p_id = db.create_product(product.dict())
    return {"id": str(p_id), "message": "Urun eklendi"}