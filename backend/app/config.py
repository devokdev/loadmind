import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/loadmind")
TARGET_DATABASE_URL = os.getenv("TARGET_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/target_db")
TARGET_APP_URL = os.getenv("TARGET_APP_URL", "http://localhost:8002")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8003"))
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
LOCUST_URL = os.getenv("LOCUST_URL", "http://localhost:8089")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
