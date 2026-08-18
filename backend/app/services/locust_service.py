import time
import requests
from config import LOCUST_URL, TARGET_APP_URL

class LocustService:
    def start_load(self, user_count: int, spawn_rate: float = 10.0):
        try:
            res = requests.post(
                f"{LOCUST_URL}/swarm",
                data={
                    "user_count": user_count,
                    "spawn_rate": spawn_rate,
                    "host": TARGET_APP_URL
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            print(f"Failed to start Locust load: {e}")
            return False

    def stop_load(self):
        try:
            res = requests.get(f"{LOCUST_URL}/stop", timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"Failed to stop Locust load: {e}")
            return False

    def get_stats(self):
        try:
            res = requests.get(f"{LOCUST_URL}/stats/requests", timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data
        except Exception as e:
            print(f"Failed to get Locust stats: {e}")
        return None

locust_service = LocustService()
