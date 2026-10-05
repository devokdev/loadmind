import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/target_db")
FAILURE_MODE = os.getenv("FAILURE_MODE", "none")

# Failure 1: Database connection pool exhaustion
# Deliberately small pool if db_pool failure is active
if FAILURE_MODE == "db_pool":
    pool_size = 20
    max_overflow = 0
    pool_timeout = 3 # small timeout to trigger failures quickly under load
else:
    pool_size = 20
    max_overflow = 10
    pool_timeout = 30

try:
    if "sqlite" in DATABASE_URL:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout
        )
        with engine.connect() as conn:
            pass
except Exception as e:
    print(f"Warning: Database connection failed ({e}). Falling back to local SQLite database.")
    engine = create_engine("sqlite:///./target.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

