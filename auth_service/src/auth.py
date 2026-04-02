from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(data: LoginData):
    # Proje basitliği için sabit kontrol (NoSQL eklenebilir)
    if data.username == "admin" and data.password == "123":
        return {"access_token": "fake-jwt-token", "status": "success"}
    raise HTTPException(status_code=401, detail="Hatali kimlik bilgileri")