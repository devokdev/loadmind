import json
from services.vector_service import vector_service
from agents.llm_client import llm_client

class Diagnostician:
    def diagnose(self, metrics: dict, failure_mode_hint: str = None, target_url: str = "") -> dict:
        # 1. Retrieve similar incidents from vector & pattern memory
        bp_users = metrics.get('breaking_point_users') or 50
        p95 = metrics.get('p95_ms') or 0.0
        err_rate = metrics.get('error_rate') or 0.0
        cpu = metrics.get('cpu_percent') or 0.0
        mem = metrics.get('memory_mb') or 0.0
        
        sig_text = f"target: {target_url}, concurrency: {bp_users}, p95_latency: {p95}ms, error_rate: {err_rate}, cpu: {cpu}%, memory: {mem}MB"
        similar = vector_service.query_similar_incidents(sig_text, n_results=2)
        
        history_context = ""
        if similar:
            history_context = "Similar past incidents retrieved from Knowledge Memory:\n"
            for s in similar:
                meta = s.get('metadata', {})
                history_context += f"- Incident {s.get('id')}: root_cause: {meta.get('primary_root_cause')}, fix: {meta.get('recommended_action')}, resolved: {meta.get('success')}\n"

        # 2. Perform LLM diagnosis if available
        if llm_client.model:
            prompt = f"""
            You are the LoadMind Autonomous Diagnostician Agent.
            Analyze the following telemetry snapshot collected during an API stress test:
            Target URL: {target_url}
            Telemetry: {json.dumps(metrics)}
            
            {history_context}
            
            Diagnose the exact primary bottleneck or root cause.
            Examples of root causes:
            - "rate_limit_throttle" (HTTP 429 Too Many Requests / upstream rate limiting)
            - "server_concurrency_exhaustion" (Worker thread or async loop starvation, gateway 502/504 timeouts)
            - "db_pool" (Database connection pool exhaustion / backend lock contention)
            - "n_plus_one" (Database N+1 relational query amplification)
            - "unbounded_cache" (Memory leak / uncontrolled cache growth)
            - "missing_index" (Unindexed database scan on high-traffic queries)
            - "blocking_async" (Blocking synchronous I/O or sleep in event loop)
            - "high_network_latency" (Downstream network transit bottleneck)

            Return a valid JSON object strictly matching this schema:
            {{
                "primary_root_cause": "root_cause_name",
                "confidence": 0.94,
                "evidence": ["evidence 1", "evidence 2", "evidence 3"],
                "alternative_causes": ["alternative cause 1"],
                "recommended_action": "concrete architectural or code recommendation"
            }}
            """
            try:
                llm_response = llm_client.generate_json(prompt)
                diag = json.loads(llm_response)
                if isinstance(diag, dict) and "primary_root_cause" in diag:
                    return diag
            except Exception as e:
                pass

        # 3. Rule-based & heuristic diagnosis fallback
        return self._rule_based_diagnosis(metrics, failure_mode_hint, history_context, target_url)

    def _rule_based_diagnosis(self, metrics: dict, hint: str, history_context: str, target_url: str) -> dict:
        if hint and hint != "none":
            cause = hint
        else:
            error_rate = metrics.get("error_rate", 0)
            p95 = metrics.get("p95_ms", 0)
            mem = metrics.get("memory_mb", 0)
            status_codes = metrics.get("status_codes", {})
            
            if status_codes.get("429", 0) > 0:
                cause = "rate_limit_throttle"
            elif status_codes.get("502", 0) > 0 or status_codes.get("504", 0) > 0:
                cause = "server_concurrency_exhaustion"
            elif mem > 500:
                cause = "unbounded_cache"
            elif error_rate > 0.15:
                cause = "db_pool"
            elif p95 > 1200:
                cause = "n_plus_one"
            elif p95 > 600:
                cause = "missing_index"
            else:
                cause = "blocking_async"

        remediations = {
            "rate_limit_throttle": "Implement token bucket rate-limiting with exponential backoff on client, or increase server API quota threshold.",
            "server_concurrency_exhaustion": "Scale worker processes (e.g. increase uvicorn/gunicorn worker count) and configure asynchronous task queuing.",
            "db_pool": "Increase database connection pool size (e.g. max_overflow/pool_size = 25) and ensure connections release immediately after execution.",
            "n_plus_one": "Use eager loading (SQLAlchemy joinedload / selectinload) to fetch related entities in a single batched SQL query.",
            "unbounded_cache": "Introduce an LRU cache eviction policy with strict max-size constraints or offload state to Redis with TTL.",
            "missing_index": "Create composite database indexes on frequently queried filtering & sorting columns.",
            "blocking_async": "Convert blocking synchronous calls to non-blocking async/await or delegate CPU-bound work to run_in_executor."
        }

        evidence = [
            f"Observed error rate: {round(metrics.get('error_rate', 0) * 100, 2)}%",
            f"Breaking point threshold: {metrics.get('breaking_point_users', 50)} concurrent synthetic users",
            f"P95 latency under stress: {round(metrics.get('p95_ms', 0), 1)} ms",
            f"Target endpoint under test: {target_url or 'Target Service'}"
        ]
        
        return {
            "primary_root_cause": cause,
            "confidence": 0.92,
            "evidence": evidence,
            "alternative_causes": ["Downstream dependency bottleneck", "Resource saturation"],
            "recommended_action": remediations.get(cause, "Optimize route concurrency and apply rate limiting.")
        }

diagnostician = Diagnostician()

