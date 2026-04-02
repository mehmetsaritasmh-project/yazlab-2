FROM python:3.10-slim

# Çalışma dizinini /app olarak belirliyoruz
WORKDIR /app

# Önce bağımlılıkları kopyalayıp yüklüyoruz (Build süresini hızlandırır)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını (src klasörü dahil) konteynere kopyalıyoruz
COPY . .

# src klasörü içindeki main.py dosyasındaki 'app' objesini çalıştırıyoruz
CMD ["uvicorn", "src.auth:app", "--host", "0.0.0.0", "--port", "8000"]