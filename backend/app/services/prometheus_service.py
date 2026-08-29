import requests
import math
from datetime import datetime
from config import PROMETHEUS_URL

class PrometheusService:
    def query_prometheus(self, query: str):
        try:
            res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query}, timeout=3)
            if res.status_code == 200:
                result = res.json().get("data", {}).get("result", [])
                if result:
                    return float(result[0]["value"][1])
        except Exception:
            pass
        return 0.0

    def get_metrics_snapshot(self):
        # Prometheus queries for target container if running in docker
        cpu_query = 'sum(rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service="target-app"}[10s])) * 100'
        mem_query = 'container_memory_usage_bytes{container_label_com_docker_compose_service="target-app"}'
        
        p50_query = 'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        p95_query = 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        p99_query = 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[10s])) by (le))'
        
        req_rate_query = 'sum(rate(http_request_duration_seconds_count[10s]))'
        error_rate_query = 'sum(rate(http_request_duration_seconds_count{status=~"5.*"}[10s])) / sum(rate(http_request_duration_seconds_count[10s]))'

        cpu_val = self.query_prometheus(cpu_query)
        mem_val = self.query_prometheus(mem_query)
        p50_val = self.query_prometheus(p50_query) * 1000
        p95_val = self.query_prometheus(p95_query) * 1000
        p99_val = self.query_prometheus(p99_query) * 1000
        req_rate_val = self.query_prometheus(req_rate_query)
        err_val = self.query_prometheus(error_rate_query)

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": round(cpu_val, 2) if not math.isnan(cpu_val) else 0.0,
            "memory_mb": round(mem_val / (1024 * 1024), 2) if not math.isnan(mem_val) else 0.0,
            "p50_ms": round(p50_val, 2) if not math.isnan(p50_val) else 0.0,
            "p95_ms": round(p95_val, 2) if not math.isnan(p95_val) else 0.0,
            "p99_ms": round(p99_val, 2) if not math.isnan(p99_val) else 0.0,
            "request_rate": round(req_rate_val, 2) if not math.isnan(req_rate_val) else 0.0,
            "error_rate": round(err_val, 4) if not math.isnan(err_val) else 0.0,
        }
        return snapshot

prometheus_service = PrometheusService()
