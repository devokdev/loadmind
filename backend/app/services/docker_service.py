import docker
import requests
from config import TARGET_APP_URL

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Docker client not initialized: {e}")
            self.client = None

    def restart_target_app(self):
        if not self.client:
            print("Docker client not available, skipping restart")
            return False
        try:
            container = self.client.containers.get("target-app")
            container.restart()
            return True
        except Exception as e:
            print(f"Failed to restart target-app: {e}")
            return False

    def set_target_failure_mode(self, mode: str):
        try:
            res = requests.post(f"{TARGET_APP_URL}/set-failure?mode={mode}", timeout=5)
            if res.status_code == 200:
                return True
        except Exception as e:
            print(f"Failed to set failure mode via HTTP: {e}")
        
        # Fallback: set env variable and restart
        if not self.client:
            return False
        try:
            container = self.client.containers.get("target-app")
            # Update env mode would require recreating, so HTTP endpoint is preferred.
            # But let's log the error.
            return False
        except Exception as e:
            print(f"Failed to set failure mode via Docker: {e}")
            return False

docker_service = DockerService()
