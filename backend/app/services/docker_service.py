import requests
from config import TARGET_APP_URL

class DockerService:
    def __init__(self):
        self.client = None
        try:
            import docker
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def restart_target_app(self):
        if not self.client:
            return False
        try:
            container = self.client.containers.get("target-app")
            container.restart()
            return True
        except Exception:
            return False

    def set_target_failure_mode(self, mode: str):
        try:
            res = requests.post(f"{TARGET_APP_URL}/set-failure?mode={mode}", timeout=3)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        return False

docker_service = DockerService()

