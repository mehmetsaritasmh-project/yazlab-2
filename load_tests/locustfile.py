from locust import HttpUser, task, between

class ProjectUser(HttpUser):
    wait_time = between(1, 2) # Her istek arası 1-2 saniye bekle

    @task
    def get_user_test(self):
        # BURADAKİ ID'Yİ KENDİ ID'NLE DEĞİŞTİR!
        user_id = "69cbb60014286632cc0911c7"
        self.client.get(f"/users/users/{user_id}")

    @task(2) # Bu görev 2 kat daha fazla çalışır
    def health_check(self):
        self.client.get("/users/health") # Varsa health check test eder