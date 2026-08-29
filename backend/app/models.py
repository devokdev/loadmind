from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Stress Run")
    target_app_url = Column(String, default="http://localhost:8002")
    http_method = Column(String, default="GET")
    request_headers = Column(JSON, nullable=True)
    payload_template = Column(Text, nullable=True)
    user_persona = Column(String, default="standard") # "standard", "aggressive_burst", "e_commerce_shopper", "heavy_read"
    load_profile = Column(String, default="step_ramp") # "step_ramp", "constant", "spike"
    max_concurrency = Column(Integer, default=100)
    duration_seconds = Column(Integer, default=30)
    
    failure_mode = Column(String, default="none")
    status = Column(String, default="pending") # "running", "completed", "failed", "stopped"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Results & Telemetry summary
    breaking_point_users = Column(Integer, nullable=True)
    p50_ms = Column(Float, nullable=True)
    p90_ms = Column(Float, nullable=True)
    p95_ms = Column(Float, nullable=True)
    p99_ms = Column(Float, nullable=True)
    avg_rps = Column(Float, nullable=True)
    peak_rps = Column(Float, nullable=True)
    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    error_rate = Column(Float, nullable=True)
    telemetry_history = Column(JSON, nullable=True)
    
    diagnoses = relationship("Diagnosis", back_populates="experiment", cascade="all, delete-orphan")
    remediations = relationship("Remediation", back_populates="experiment", cascade="all, delete-orphan")

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    primary_root_cause = Column(String)
    confidence = Column(Float)
    evidence = Column(JSON)
    alternative_causes = Column(JSON)
    recommended_action = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    experiment = relationship("Experiment", back_populates="diagnoses")

class Remediation(Base):
    __tablename__ = "remediations"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    proposed_remediation = Column(Text)
    patch_diff = Column(Text)
    architecture_advice = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    
    # Verification metrics
    verified = Column(Boolean, default=False)
    success = Column(Boolean, nullable=True)
    latency_improvement_percent = Column(Float, nullable=True)
    error_rate_before = Column(Float, nullable=True)
    error_rate_after = Column(Float, nullable=True)
    breaking_point_before = Column(Integer, nullable=True)
    breaking_point_after = Column(Integer, nullable=True)
    
    experiment = relationship("Experiment", back_populates="remediations")

class LearnedPattern(Base):
    __tablename__ = "learned_patterns"
    id = Column(Integer, primary_key=True, index=True)
    signature_hash = Column(String, unique=True, index=True)
    title = Column(String)
    root_cause = Column(String)
    symptoms = Column(JSON) # e.g. ["latency spike > 1.5s", "error rate > 5%", "connection timeouts"]
    remediation_strategy = Column(Text)
    success_rate = Column(Float, default=1.0)
    times_encountered = Column(Integer, default=1)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

