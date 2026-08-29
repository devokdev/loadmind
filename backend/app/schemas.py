from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class ExperimentCreate(BaseModel):
    name: Optional[str] = "Stress Run"
    target_app_url: str = Field(default="http://localhost:8002", description="Target API endpoint or base URL")
    http_method: Optional[str] = "GET"
    request_headers: Optional[Dict[str, str]] = None
    payload_template: Optional[str] = None
    user_persona: Optional[str] = "standard" # standard, aggressive_burst, e_commerce_shopper, heavy_read
    load_profile: Optional[str] = "step_ramp" # step_ramp, constant, spike
    max_concurrency: Optional[int] = 100
    duration_seconds: Optional[int] = 30
    failure_mode: Optional[str] = "none"

class MetricPoint(BaseModel):
    timestamp: str
    users: int
    rps: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    cpu_percent: Optional[float] = 0.0
    memory_mb: Optional[float] = 0.0
    status_codes: Optional[Dict[str, int]] = None

class ExperimentResponse(BaseModel):
    id: int
    name: Optional[str]
    target_app_url: str
    http_method: Optional[str]
    user_persona: Optional[str]
    load_profile: Optional[str]
    max_concurrency: Optional[int]
    duration_seconds: Optional[int]
    failure_mode: str
    status: str
    created_at: datetime
    breaking_point_users: Optional[int] = None
    p50_ms: Optional[float] = None
    p90_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    avg_rps: Optional[float] = None
    peak_rps: Optional[float] = None
    total_requests: Optional[int] = 0
    total_errors: Optional[int] = 0
    error_rate: Optional[float] = None
    telemetry_history: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
        orm_mode = True

class DiagnosisResponse(BaseModel):
    id: int
    experiment_id: int
    primary_root_cause: str
    confidence: float
    evidence: List[str]
    alternative_causes: List[str]
    recommended_action: str
    created_at: datetime

    class Config:
        orm_mode = True

class RemediationResponse(BaseModel):
    id: int
    experiment_id: int
    proposed_remediation: str
    patch_diff: Optional[str] = None
    architecture_advice: Optional[str] = None
    is_applied: bool
    applied_at: Optional[datetime] = None
    verified: bool
    success: Optional[bool] = None
    latency_improvement_percent: Optional[float] = None
    error_rate_before: Optional[float] = None
    error_rate_after: Optional[float] = None
    breaking_point_before: Optional[int] = None
    breaking_point_after: Optional[int] = None

    class Config:
        orm_mode = True

class LearnedPatternResponse(BaseModel):
    id: int
    signature_hash: str
    title: str
    root_cause: str
    symptoms: List[str]
    remediation_strategy: str
    success_rate: float
    times_encountered: int
    last_seen_at: datetime

    class Config:
        orm_mode = True

