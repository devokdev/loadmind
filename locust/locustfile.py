import os
import random
from locust import HttpUser, task, between

class ECommerceUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def browse_products(self):
        self.client.get("/products")

    @task(3)
    def get_recommendations(self):
        self.client.get("/recommendations")

    @task(2)
    def view_orders(self):
        user_id = random.randint(1, 100)
        self.client.get(f"/orders?user_id={user_id}")

    @task(1)
    def checkout_process(self):
        self.client.get("/checkout/process")

    @task(1)
    def check_db_status(self):
        self.client.get("/db-status")
