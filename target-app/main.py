import os
import time
import asyncio
import random
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_fastapi_instrumentator import Instrumentator

from database import get_db, engine, FAILURE_MODE
import models

# Re-create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="LoadMind Target Application")

# Instrument app with Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Global variables for dynamic failure modes
CURRENT_FAILURE_MODE = os.getenv("FAILURE_MODE", "none")
UNBOUNDED_CACHE = []

@app.on_event("startup")
def seed_data():
    db = next(get_db())
    # Seed Vendors if empty
    if db.query(models.Vendor).count() == 0:
        vendors = [models.Vendor(name=f"Vendor {i}", contact=f"vendor{i}@shop.com") for i in range(1, 51)]
        db.add_all(vendors)
        db.commit()

    # Seed Products if empty
    if db.query(models.Product).count() == 0:
        vendors = db.query(models.Vendor).all()
        products = [
            models.Product(name=f"Product {i}", price=random.randint(10, 1000), vendor_id=random.choice(vendors).id)
            for i in range(1, 101)
        ]
        db.add_all(products)
        db.commit()

    # Seed Users if empty
    if db.query(models.User).count() == 0:
        users = [models.User(username=f"user_{i}") for i in range(1, 101)]
        db.add_all(users)
        db.commit()

    # Seed Orders if empty
    if db.query(models.Order).count() == 0:
        users = db.query(models.User).all()
        orders = [
            models.Order(
                user_id=random.choice(users).id,
                item_details=f"Item details for order {i}",
                total_amount=random.randint(20, 500)
            )
            for i in range(1, 10001) # Seed 10,000 orders to show missing index latency
        ]
        db.add_all(orders)
        db.commit()

    # Handle missing/existing index dynamically for Failure 4
    # If missing_index is active, drop index. Else, create index.
    try:
        if CURRENT_FAILURE_MODE == "missing_index":
            db.execute(text("DROP INDEX IF EXISTS idx_orders_user_id;"))
        else:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);"))
        db.commit()
    except Exception as e:
        print(f"Index operation error: {e}")
        db.rollback()

@app.get("/health")
def health_check():
    return {"status": "ok", "failure_mode": CURRENT_FAILURE_MODE}

@app.post("/set-failure")
def set_failure_mode(mode: str):
    global CURRENT_FAILURE_MODE
    valid_modes = ["db_pool", "n_plus_one", "unbounded_cache", "missing_index", "blocking_async", "none"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail="Invalid failure mode")
    
    CURRENT_FAILURE_MODE = mode
    
    # Toggle index dynamically
    db = next(get_db())
    try:
        if mode == "missing_index":
            db.execute(text("DROP INDEX IF EXISTS idx_orders_user_id;"))
        else:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "failure mode updated", "current_mode": CURRENT_FAILURE_MODE}

# Route 1: Products (N+1 Query Demonstration)
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    if CURRENT_FAILURE_MODE == "n_plus_one":
        # N+1 query problem: fetch products then query vendor for each product individually
        products = db.query(models.Product).all()
        result = []
        for p in products:
            # Deliberately run query inside loop
            vendor = db.query(models.Vendor).filter(models.Vendor.id == p.vendor_id).first()
            result.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "vendor": {"id": vendor.id, "name": vendor.name} if vendor else None
            })
        return result
    else:
        # Optimized: Eager load relations
        # Using join/options or simple joinedload
        from sqlalchemy.orm import joinedload
        products = db.query(models.Product).options(joinedload(models.Product.vendor)).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "vendor": {"id": p.vendor.id, "name": p.vendor.name} if p.vendor else None
            } for p in products
        ]

# Route 2: Recommendations (Unbounded Cache / memory growth)
@app.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    if CURRENT_FAILURE_MODE == "unbounded_cache":
        # Leak memory by appending large blocks to global list
        large_block = os.urandom(1024 * 256) # 256 KB per request
        UNBOUNDED_CACHE.append(large_block)
    
    # Just return some products
    products = db.query(models.Product).limit(5).all()
    return {"recommendations": [p.name for p in products], "cache_size_items": len(UNBOUNDED_CACHE)}

# Route 3: Orders (Missing Index / slow query on large dataset)
@app.get("/orders")
def get_orders(user_id: int = None, db: Session = Depends(get_db)):
    # If user_id is not provided, choose a random one
    if not user_id:
        user_id = random.randint(1, 100)
    
    # Large dataset filter query
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    return {"user_id": user_id, "orders_count": len(orders)}

# Route 4: Checkout Process (Blocking Synchronous Call in Async Route)
@app.get("/checkout/process")
async def checkout_process():
    if CURRENT_FAILURE_MODE == "blocking_async":
        # Synchronously block the event loop
        time.sleep(1.0)
        return {"status": "processed", "type": "blocking"}
    else:
        # Properly yield execution back to the event loop
        await asyncio.sleep(1.0)
        return {"status": "processed", "type": "async"}

# Route 5: Database Connection Pool Exhaustion (Route holding DB connections)
@app.get("/db-status")
def get_db_status(db: Session = Depends(get_db)):
    if CURRENT_FAILURE_MODE == "db_pool":
        # Sleep while holding DB session open to simulate a slow operation keeping DB connection occupied
        db.execute(text("SELECT pg_sleep(2.0);"))
    else:
        db.execute(text("SELECT 1;"))
    return {"db_pool": "healthy"}
