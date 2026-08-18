import requests
from datetime import datetime, timedelta
from config import PROMETHEUS_URL

class PrometheusService:
    def query_prometheus(self, query: str):
        try:
            res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query}, timeout=5)
            if res.status_code == 200:
                result = res.json().get("data", {}).get("result", [])
                if result:
                    return float(result[0]["value"][1])
        except Exception as e:
            print(f"Prometheus query failed for '{query}': {e}")
        return 0.0

    def get_metrics_snapshot(self):
        # Queries for target-app metrics
        cpu_query = 'sum(rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service="target-app"}[10s])) * 100'
        mem_query = 'container_memory_usage_bytes{container_label_com_docker_compose_service="target-app"}'
        
        # FastAPI HTTP metrics
        p50_query = 'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        p95_query = 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        p99_query = 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        
        req_rate_query = 'sum(rate(http_request_duration_seconds_count[10s]))'
        error_rate_query = 'sum(rate(http_request_duration_seconds_count{status=~"5.*"}[10s])) / sum(rate(http_request_duration_seconds_count[10s]))'

        # PostgreSQL db-pool connection metrics (from target-app custom metrics if any, or simulated wait/active connection queries)
        # Let's read PG metrics. If we cannot read from prometheus directly, we query the DB or we write queries.
        # Let's query target-postgres pg_stat_activity using standard engine if needed, or query prometheus if PostgreSQL exporter is active.
        # Since we want it robust, we'll query target-app db status endpoint or query pg_stat_activity directly!
        # Let's check target db connections:
        db_connections_query = 'sum(pg_stat_database_numbackends)' # or similar

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": round(self.query_prometheus(cpu_query), 2),
            "memory_mb": round(self.query_prometheus(mem_query) / (1024 * 1024), 2),
            "p50_ms": round(self.query_prometheus(p50_query) * 1000, 2),
            "p95_ms": round(self.query_prometheus(p95_query) * 1000, 2),
            "p99_ms": round(self.query_prometheus(p99_query) * 1000, 2),
            "request_rate": round(self.query_prometheus(req_rate_query), 2),
            "error_rate": round(self.query_prometheus(error_rate_query), 4),
        }
        
        # If latency queries return NaN, set to 0
        for k in ["p50_ms", "p95_ms", "p99_ms"]:
            if snapshot[k] < 0 or snapshot[k] != snapshot[k]: # NaN check
                snapshot[k] = 0.0
        if snapshot["error_rate"] != snapshot["error_rate"]:
            snapshot["error_rate"] = 0.0

        return snapshot

prometheus_service = PrometheusService()
