import httpx
import time
import sys
import os
import json
from fastapi import FastAPI, Request, Response, HTTPException


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import DispatcherDatabase 
except ImportError:
    from .database import DispatcherDatabase


app = FastAPI(title="YazLab2 Dispatcher (API Gateway)", redirect_slashes=False)
db = DispatcherDatabase()

# Mikroservis adresleri (Docker-compose servis adları)
microservices = {
    "users": "http://user_service:8000",
    "products": "http://product_service:8000",
    "auth": "http://auth_service:8000"
}

# Alt servislerin beklediği güvenlik anahtarı
DISPATCHER_SECRET = "proje_ozel_anahtar_123"



@app.get("/")
async def root():
    """
    Tarayıcıdan localhost:8000 yazıldığında 404 alınmasını engeller.
    """
    return {
        "status": "online",
        "service": "API Gateway",
        "available_endpoints": ["/health", "/metrics", "/auth", "/users", "/products"]
    }

# --- 2. ÖZEL ROTALAR ---

@app.get("/metrics")
@app.get("/metrics/")
async def get_metrics():
    """
    Grafana'nın 'JSON API' veya 'Infinity' pluginleri ile 
    grafik oluşturabilmesi için ham log verilerini döner.
    """
    try:
        logs = db.get_all_logs()
        return logs
    except Exception as e:
        return {"error": f"Log okuma hatası: {str(e)}"}

@app.get("/health")
@app.get("/health/")
async def health():
    """Sistemin durumunu kontrol eder."""
    return {
        "status": "ok", 
        "message": "Dispatcher is alive", 
        "timestamp": time.time()
    }

# --- 3. ANA GATEWAY MEKANİZMASI ---

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(request: Request, service: str, path: str):
    # KORUMA: Statik rotaların yanlışlıkla yakalanmasını önle
    if service == "health": return await health()
    if service == "metrics": return await get_metrics()

    # 1. Servis Kontrolü
    if service not in microservices:
        raise HTTPException(status_code=404, detail=f"Servis tanımlı değil: {service}")

    # 2. Yetkilendirme (Auth hariç her yerde token zorunlu)
    if service != "auth":
        token = request.headers.get("Authorization")
        if not token or not db.check_token(token):
            return Response(
                content=json.dumps({"error": "Yetkisiz erişim: Geçersiz token"}), 
                status_code=401, 
                media_type="application/json"
            )

    # 3. Path Temizliği
    clean_path = path
    if path.startswith(f"{service}/"):
        clean_path = path.replace(f"{service}/", "", 1)
    
    target_url = f"{microservices[service]}/{clean_path}"
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            # Gelen isteği ilgili servise iletir
            body = await request.body()
            
            
            new_headers = dict(request.headers)
            
            if "host" in new_headers:
                del new_headers["host"]
            
            
            new_headers["x-dispatcher-key"] = DISPATCHER_SECRET
            
            proxy_res = await client.request(
                method=request.method,
                url=target_url,
                headers=new_headers,
                content=body,
                timeout=10.0
            )
            
            response_time = (time.time() - start_time) * 1000 
            
            # 4. Loglama
            db.log_request(
                method=request.method,
                path=f"/{service}/{clean_path}",
                status_code=proxy_res.status_code,
                response_time=response_time
            )

            return Response(
                content=proxy_res.content,
                status_code=proxy_res.status_code,
                headers=dict(proxy_res.headers)
            )

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            return Response(
                content=json.dumps({"error": f"{service} servisine ulaşılamıyor: {str(e)}"}), 
                status_code=533, 
                media_type="application/json"
            )
        except Exception as e:
            return Response(
                content=json.dumps({"error": f"Gateway Hatası: {str(e)}"}), 
                status_code=500, 
                media_type="application/json"
            )