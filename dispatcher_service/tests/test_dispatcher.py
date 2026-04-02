# dispatcher_service/tests/test_dispatcher.py
import pytest
import requests

# Bu test, Dispatcher'ın (localhost:8000) gelen isteği 
# Auth servisine yönlendirip yönlendirmediğini test eder.
# Henüz kod yazılmadığı için bu test BAŞARISIZ (RED) olacaktır.

def test_dispatcher_routing_to_auth():
    # Dispatcher URL'i
    url = "http://localhost:8000/auth/login"
    
    try:
        # Sahte bir login isteği gönderiyoruz
        response = requests.post(url, json={"user": "test", "pass": "123"})
        # Beklenen durum: Dispatcher'ın isteği başarıyla iletmesi
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        # Servis henüz kurulu olmadığı için bağlantı hatası verecektir
        pytest.fail("Dispatcher henüz çalışmıyor - BEKLENEN TDD RED DURUMU")
