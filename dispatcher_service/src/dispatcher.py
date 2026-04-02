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


SERVICES = {
    "users": "http://user_service:8001",
    "products": "http://product_service:8002",
    "auth": "http://auth_service:8003"  
}

DISPATCHER_SECRET = "proje_ozel_anahtar_123"

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "API Gateway",
        "available_endpoints": ["/health", "/metrics", "/auth", "/users", "/products"]
    }

# --- PROMETHEUS UYUMLU METRICS ---
@app.get("/metrics")
@app.get("/metrics/")
async def get_metrics():
    try:
        logs = db.get_all_logs()
        prometheus_lines = []
        if not logs:
            return Response(content="# No logs available yet", media_type="text/plain")

        for log in logs:
            method = log.get("method", "UNKNOWN")
            path = log.get("path", "unknown")
            status = log.get("status_code", 0)
            duration = log.get("response_time_ms", 0)
            
            line = f'http_request_duration_ms{{method="{method}",path="{path}",status="{status}"}} {duration}'
            prometheus_lines.append(line)
        
        output = "\n".join(prometheus_lines)
        return Response(content=output, media_type="text/plain")
    except Exception as e:
        return Response(content=f"# Metrics Error: {str(e)}", status_code=500, media_type="text/plain")

@app.get("/health")
@app.get("/health/")
async def health():
    return {"status": "ok", "message": "Dispatcher is alive", "timestamp": time.time()}

# --- ANA GATEWAY MEKANİZMASI ---
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(request: Request, service: str, path: str):
    # 1. KORUMA: Statik rotaların yanlışlıkla yakalanmasını önle
    if service == "health": return await health()
    if service == "metrics": return await get_metrics()

    # 2. SERVİS KONTROLÜ
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Servis tanımlı değil: {service}")

    # 3. TOKEN MUAFİYET KONTROLÜ
    # Yolun 'health' olup olmadığını kontrol et (Örn: /users/health -> path="health")
    clean_path = path.strip("/")
    is_health_check = (clean_path == "health")
    is_auth_route = (service == "auth")

    # Auth ve Health dışındaki her şey için token kontrolü
    if not is_auth_route and not is_health_check:
        token = request.headers.get("Authorization")
        if not token or not db.check_token(token):
            return Response(
                content=json.dumps({"error": "Yetkisiz erişim: Geçersiz veya eksik token"}), 
                status_code=401, 
                media_type="application/json"
            )

    # 4. HEDEF URL OLUŞTURMA
    
    target_url = f"{SERVICES[service]}/{clean_path}"
    
    
    print(f"DEBUG: Proxying {request.method} request to -> {target_url}")

    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            body = await request.body()
            new_headers = dict(request.headers)
            
            # Docker iç ağında 'host' header'ı çakışmaya neden olabilir, temizliyoruz
            if "host" in new_headers:
                del new_headers["host"]
            
            
            new_headers["x-dispatcher-key"] = DISPATCHER_SECRET
            
            proxy_res = await client.request(
                method=request.method,
                url=target_url,
                headers=new_headers,
                content=body,
                params=request.query_params, # Sorgu parametrelerini (?id=1 vb.) aktarır
                timeout=10.0
            )
            
            # Yanıt süresi hesaplama ve veritabanına loglama
            response_time = (time.time() - start_time) * 1000 
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

        except Exception as e:
            return Response(
                content=json.dumps({"error": f"Gateway Hatası: {str(e)}"}), 
                status_code=500, 
                media_type="application/json"
            )