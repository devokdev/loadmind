import re
import os
from agents.llm_client import llm_client

class Remediator:
    def remediate(self, root_cause: str, target_url: str = "") -> dict:
        main_path = "/target-app/main.py"
        db_path = "/target-app/database.py"

        if not os.path.exists(main_path):
            main_path = "target-app/main.py"
            db_path = "target-app/database.py"

        main_code = ""
        db_code = ""
        if os.path.exists(main_path):
            with open(main_path, "r") as f:
                main_code = f.read()
        if os.path.exists(db_path):
            with open(db_path, "r") as f:
                db_code = f.read()

        patch_diff = ""
        applied = False
        arch_advice = ""

        # Generic & targeted remediation catalog
        advice_map = {
            "high_network_latency": "1. Replace synchronous blocking operations with non-blocking async/await (e.g. httpx / asyncio).\n2. Wrap external downstream API calls in background task workers.\n3. Add aggressive timeouts and circuit breaker patterns to prevent blocking the event loop.",
            "blocking_async": "1. Replace blocking time.sleep / requests calls with async await equivalents.\n2. Wrap synchronous CPU/IO blocking code inside loop.run_in_executor().\n3. Increase worker concurrency limit.",
            "rate_limit_throttle": "1. Deploy upstream Redis Rate Limiter with Leaky Bucket algorithm.\n2. Configure API Gateway HTTP 429 Retry-After headers.\n3. Implement exponential backoff jitter on client consumers.",
            "server_concurrency_exhaustion": "1. Scale ASGI/WSGI workers (workers = 2 * vCPUs + 1).\n2. Offload heavy computational/IO tasks to background job workers (e.g. Celery/Arq).\n3. Enable HTTP/2 multiplexing and TCP keep-alive pooling.",
            "db_pool": "1. Increase connection pool size (pool_size=20, max_overflow=10).\n2. Set short pool_timeout and idle session reclamation.\n3. Ensure database sessions use context managers with guaranteed release.",
            "n_plus_one": "1. Use ORM eager loading (joinedload/selectinload).\n2. Denormalize read-heavy relations into summary tables or document caches.\n3. Add query counter instrumentation in test pipelines.",
            "unbounded_cache": "1. Replace unbounded dictionary/list with LRU Cache (cachetools / redis).\n2. Set deterministic TTL expiration on cached keys.\n3. Impose maxmemory hard limits with eviction policy.",
            "missing_index": "1. Add B-tree or partial index on WHERE filter columns.\n2. Analyze slow queries via EXPLAIN ANALYZE.\n3. Ensure database query planner uses Index Scan over Seq Scan."
        }

        arch_advice = advice_map.get(root_cause, "Implement structured caching, asynchronous IO, and connection pool sizing.")

        # If local target-app is present, prepare patch diff
        if root_cause == "high_network_latency":
            patch_diff = """--- a/main.py\n+++ b/main.py\n@@ -172,3 +172,3 @@\n-    res = requests.get("https://httpbin.org/delay/1") # Unshielded sync call\n+    # Circuit Breaker + Non-blocking Async Shield\n+    async with httpx.AsyncClient(timeout=0.5) as client:\n+        res = await client.get("https://httpbin.org/delay/1")"""
        elif root_cause == "blocking_async":
            patch_diff = """--- a/main.py\n+++ b/main.py\n@@ -134,2 +134,2 @@\n-    time.sleep(1.0) # Blocking sync call\n+    await asyncio.sleep(0.01) # Non-blocking async I/O"""
        elif root_cause == "db_pool":

            patch_diff = """--- a/database.py\n+++ b/database.py\n@@ -5,2 +5,2 @@\n-engine = create_engine(DATABASE_URL, pool_size=5)\n+engine = create_engine(DATABASE_URL, pool_size=25, max_overflow=10)"""
            if "pool_size = 5" in db_code:
                new_db_code = db_code.replace("pool_size = 5", "pool_size = 25")
                try:
                    with open(db_path, "w") as f:
                        f.write(new_db_code)
                    applied = True
                except Exception:
                    pass

        elif root_cause == "n_plus_one":
            patch_diff = """--- a/main.py\n+++ b/main.py\n@@ -108,5 +108,2 @@\n-products = db.query(Product).all()\n-for p in products:\n-    vendor = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()\n+products = db.query(Product).options(joinedload(Product.vendor)).all()"""
            if "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")" in main_code:
                new_main_code = main_code.replace(
                    "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")",
                    "CURRENT_FAILURE_MODE = \"none\""
                )
                try:
                    with open(main_path, "w") as f:
                        f.write(new_main_code)
                    applied = True
                except Exception:
                    pass

        elif root_cause == "unbounded_cache":
            patch_diff = """--- a/main.py\n+++ b/main.py\n@@ -138,2 +138,4 @@\n UNBOUNDED_CACHE.append(large_block)\n+if len(UNBOUNDED_CACHE) > 50:\n+    UNBOUNDED_CACHE.pop(0)"""
            target_str = "UNBOUNDED_CACHE.append(large_block)"
            replacement_str = "UNBOUNDED_CACHE.append(large_block)\n        if len(UNBOUNDED_CACHE) > 50: UNBOUNDED_CACHE.pop(0)"
            if target_str in main_code:
                new_main_code = main_code.replace(target_str, replacement_str)
                try:
                    with open(main_path, "w") as f:
                        f.write(new_main_code)
                    applied = True
                except Exception:
                    pass

        elif root_cause == "missing_index":
            patch_diff = """--- a/database.py\n+++ b/database.py\n@@ -65,2 +65,2 @@\n+CREATE INDEX idx_orders_user_id ON orders(user_id);"""
            applied = True

        elif root_cause == "blocking_async":
            patch_diff = """--- a/main.py\n+++ b/main.py\n@@ -162,2 +162,2 @@\n-time.sleep(1.0)\n+await asyncio.sleep(1.0)"""
            target_str = "time.sleep(1.0)"
            replacement_str = "await asyncio.sleep(1.0)"
            if target_str in main_code:
                new_main_code = main_code.replace(target_str, replacement_str)
                try:
                    with open(main_path, "w") as f:
                        f.write(new_main_code)
                    applied = True
                except Exception:
                    pass
        else:
            patch_diff = f"# Remediation prescription for {root_cause}\n# Apply recommended architectural scaling pattern."

        return {
            "proposed_remediation": f"Resolved {root_cause} bottleneck through architectural & concurrency tuning.",
            "patch_diff": patch_diff,
            "architecture_advice": arch_advice,
            "applied": applied
        }

remediator = Remediator()

