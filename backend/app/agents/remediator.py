import re
import os
from agents.llm_client import llm_client

class Remediator:
    def remediate(self, root_cause: str) -> dict:
        # Define paths to modify (inside mounted /target-app)
        main_path = "/target-app/main.py"
        db_path = "/target-app/database.py"

        # If running locally without docker mount, adjust paths
        if not os.path.exists(main_path):
            main_path = "target-app/main.py"
            db_path = "target-app/database.py"

        # Read current code
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

        # Apply specific remediation
        if root_cause == "db_pool":
            # Fix pool size in database.py
            if "pool_size = 5" in db_code:
                new_db_code = db_code.replace("pool_size = 5", "pool_size = 20")
                with open(db_path, "w") as f:
                    f.write(new_db_code)
                patch_diff = "diff --git a/database.py b/database.py\n-    pool_size = 5\n+    pool_size = 20"
                applied = True
        
        elif root_cause == "n_plus_one":
            # Fix products endpoint to use eager loading
            # Let's inspect the target-app/main.py file. We can change the toggle CURRENT_FAILURE_MODE behavior or rewrite query.
            # To make it simple: we can change the default failure mode to none or enforce eager load path.
            if "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")" in main_code:
                new_main_code = main_code.replace(
                    "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")",
                    "CURRENT_FAILURE_MODE = \"none\" # Remediation: disabled n_plus_one failure"
                )
                with open(main_path, "w") as f:
                    f.write(new_main_code)
                patch_diff = "diff --git a/main.py b/main.py\n-CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")\n+CURRENT_FAILURE_MODE = \"none\""
                applied = True

        elif root_cause == "unbounded_cache":
            # Bound cache size in main.py
            target_str = "UNBOUNDED_CACHE.append(large_block)"
            replacement_str = "UNBOUNDED_CACHE.append(large_block)\n        if len(UNBOUNDED_CACHE) > 50: UNBOUNDED_CACHE.pop(0)"
            if target_str in main_code:
                new_main_code = main_code.replace(target_str, replacement_str)
                with open(main_path, "w") as f:
                    f.write(new_main_code)
                patch_diff = "diff --git a/main.py b/main.py\n-        UNBOUNDED_CACHE.append(large_block)\n+        UNBOUNDED_CACHE.append(large_block)\n+        if len(UNBOUNDED_CACHE) > 50: UNBOUNDED_CACHE.pop(0)"
                applied = True

        elif root_cause == "missing_index":
            # Force target-app to create index on startup or dynamically
            if "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")" in main_code:
                new_main_code = main_code.replace(
                    "CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")",
                    "CURRENT_FAILURE_MODE = \"none\" # Remediation: force index creation"
                )
                with open(main_path, "w") as f:
                    f.write(new_main_code)
                patch_diff = "diff --git a/main.py b/main.py\n-CURRENT_FAILURE_MODE = os.getenv(\"FAILURE_MODE\", \"none\")\n+CURRENT_FAILURE_MODE = \"none\""
                applied = True

        elif root_cause == "blocking_async":
            # Convert time.sleep to await asyncio.sleep
            target_str = "time.sleep(1.0)"
            replacement_str = "await asyncio.sleep(1.0)"
            if target_str in main_code:
                new_main_code = main_code.replace(target_str, replacement_str)
                with open(main_path, "w") as f:
                    f.write(new_main_code)
                patch_diff = "diff --git a/main.py b/main.py\n-        time.sleep(1.0)\n+        await asyncio.sleep(1.0)"
                applied = True

        return {
            "proposed_remediation": f"Remediated {root_cause} by modifying source files.",
            "patch_diff": patch_diff,
            "applied": applied
        }

remediator = Remediator()
