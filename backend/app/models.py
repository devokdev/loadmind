from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    target_app_url = Column(String)
    failure_mode = Column(String)
    status = Column(String) # "running", "completed", "failed"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Results
    breaking_point_users = Column(Integer, nullable=True)
    p50_ms = Column(Float, nullable=True)
    p95_ms = Column(Float, nullable=True)
    p99_ms = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    
    diagnoses = relationship("Diagnosis", back_populates="experiment")
    remediations = relationship("Remediation", back_populates="experiment")

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    primary_root_cause = Column(String)
    confidence = Column(Float)
    evidence = Column(JSON)
    alternative_causes = Column(JSON)
    recommended_action = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    experiment = relationship("Experiment", back_populates="diagnoses")

class Remediation(Base):
    __tablename__ = "remediations"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    proposed_remediation = Column(String)
    patch_diff = Column(String)
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
