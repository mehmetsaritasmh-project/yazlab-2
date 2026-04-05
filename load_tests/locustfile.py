from locust import HttpUser, task, between

class ProjectUser(HttpUser):
    wait_time = between(1, 2) 

    @task
    def get_user_test(self):
    
        user_id = "69cbb60014286632cc0911c7"
        self.client.get(f"/users/users/{user_id}")

    @task(2) 
    def health_check(self):
        self.client.get("/users/health") 
