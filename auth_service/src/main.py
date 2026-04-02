from fastapi import FastAPI, HTTPException, Body
from database import AuthDatabase 
import uuid

app = FastAPI(title="Auth Service")
db = AuthDatabase()

@app.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    if username == "admin" and password == "password123":
        access_token = str(uuid.uuid4())
        db.save_token(username, access_token)
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")

@app.get("/validate")
async def validate(token: str):
    is_valid = db.check_token(token)
    if is_valid:
        return {"valid": True, "username": is_valid["username"]}
    return {"valid": False}