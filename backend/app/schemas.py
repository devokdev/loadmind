from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class ExperimentCreate(BaseModel):
    failure_mode: str

class ExperimentResponse(BaseModel):
    id: int
    target_app_url: str
    failure_mode: str
    status: str
    created_at: datetime
    breaking_point_users: Optional[int]
    p50_ms: Optional[float]
    p95_ms: Optional[float]
    p99_ms: Optional[float]
    error_rate: Optional[float]

    class Config:
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
    patch_diff: str
    is_applied: bool
    applied_at: Optional[datetime]
    verified: bool
    success: Optional[bool]
    latency_improvement_percent: Optional[float]
    error_rate_before: Optional[float]
    error_rate_after: Optional[float]
    breaking_point_before: Optional[int]
    breaking_point_after: Optional[int]

    class Config:
        orm_mode = True
