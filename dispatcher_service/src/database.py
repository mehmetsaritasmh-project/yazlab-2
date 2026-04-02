from pymongo import MongoClient
from datetime import datetime
import time

class DispatcherDatabase:
    """
    Dispatcher servisi için NoSQL (MongoDB) veritabanı yönetim sınıfı.
    Grafana JSON API ile tam uyumlu hale getirilmiştir.
    """
    def __init__(self):
        # Bağlantı hatalarını önlemek için try-except içine alıyoruz
        try:
            # docker-compose içindeki servis adıyla eşleşmeli: dispatcher_db_container
            self.client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=5000)
            self.db = self.client["dispatcher_db"]
            self.logs = self.db["traffic_logs"]
            # Bağlantıyı test et
            self.client.admin.command('ping')
        except Exception as e:
            print(f"KRİTİK HATA: MongoDB'ye bağlanılamadı: {e}")

    def log_request(self, method, path, status_code, response_time):
        """
        Gelen her isteği kaydeder. response_time milisaniye (ms) cinsindendir.
        """
        log_data = {
            "timestamp": datetime.utcnow(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": response_time
        }
        try:
            self.logs.insert_one(log_data)
        except Exception as e:
            print(f"Log yazma hatası: {e}")

    def check_token(self, token):
        """
        Auth servisi tarafından bu DB'ye yazılan aktif tokenları kontrol eder.
        """
        try:
            auth_collection = self.db["active_tokens"]
            # Token kontrolü (Basit bir find_one yeterli)
            user_session = auth_collection.find_one({"token": token})
            return user_session is not None
        except:
            return False

    def get_all_logs(self):
        """
        Grafana JSON API eklentisinin okuyabileceği formatta son 100 logu döner.
        """
        try:
            # _id: 0 ile MongoDB'nin özel ID formatını siliyoruz (JSON hata vermesin diye)
            # -1 ile en yeni kayıtları önce getiriyoruz
            logs_cursor = self.logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(100)
            
            logs_list = list(logs_cursor)
            
            
            for log in logs_list:
                if isinstance(log.get("timestamp"), datetime):
                    log["timestamp"] = log["timestamp"].isoformat() + "Z" # Grafana Z (Zulu/UTC) bekler
            
            return logs_list
        except Exception as e:
            print(f"Grafana verisi çekilirken hata oluştu: {e}")
            return []