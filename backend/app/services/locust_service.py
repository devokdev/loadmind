import time
import requests
from config import LOCUST_URL, TARGET_APP_URL

class LocustService:
    def is_available(self) -> bool:
        try:
            res = requests.get(f"{LOCUST_URL}/stats/requests", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def start_load(self, user_count: int, spawn_rate: float = 10.0, host: str = None):
        target = host or TARGET_APP_URL
        try:
            res = requests.post(
                f"{LOCUST_URL}/swarm",
                data={
                    "user_count": user_count,
                    "spawn_rate": spawn_rate,
                    "host": target
                },
                timeout=5
            )
            return res.status_code == 200
        except Exception as e:
            return False

    def stop_load(self):
        try:
            res = requests.get(f"{LOCUST_URL}/stop", timeout=3)
            return res.status_code == 200
        except Exception as e:
            return False

    def get_stats(self):
        try:
            res = requests.get(f"{LOCUST_URL}/stats/requests", timeout=3)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            pass
        return None

locust_service = LocustService()

