import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current and parent directories
env_paths = [
    Path(".env"),
    Path("../.env"),
    Path("../../.env"),
    Path(__file__).resolve().parent.parent.parent / ".env"
]
for p in env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p)
        break

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/loadmind")
TARGET_DATABASE_URL = os.getenv("TARGET_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/target_db")
TARGET_APP_URL = os.getenv("TARGET_APP_URL", "http://localhost:8002")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8003"))
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOCUST_URL = os.getenv("LOCUST_URL", "http://localhost:8089")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")




