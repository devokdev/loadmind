import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
import models
from services.vector_service import vector_service

class Learner:
    def learn(self, db: Session, experiment_id: int, remediation_id: int = None):
        exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
        diag = db.query(models.Diagnosis).filter(models.Diagnosis.experiment_id == experiment_id).first()
        rem = db.query(models.Remediation).filter(models.Remediation.experiment_id == experiment_id).first() if not remediation_id else db.query(models.Remediation).filter(models.Remediation.id == remediation_id).first()
        
        if not exp or not diag:
            return False

        root_cause = diag.primary_root_cause
        rec_action = diag.recommended_action
        is_success = rem.success if (rem and rem.success is not None) else True

        # Construct failure signature
        signature_text = f"target: {exp.target_app_url}, bp_users: {exp.breaking_point_users or 50}, p95: {exp.p95_ms or 0}ms, error_rate: {exp.error_rate or 0}, cause: {root_cause}"
        sig_hash = hashlib.md5(f"{root_cause}_{exp.breaking_point_users}_{round(exp.error_rate or 0, 2)}".encode()).hexdigest()[:12]

        # Metadata
        metadata = {
            "experiment_id": exp.id,
            "target_url": exp.target_app_url,
            "failure_mode": exp.failure_mode,
            "primary_root_cause": root_cause,
            "recommended_action": rec_action,
            "success": is_success,
            "breaking_point_before": (rem.breaking_point_before if rem else exp.breaking_point_users) or 50,
            "breaking_point_after": (rem.breaking_point_after if rem else (exp.breaking_point_users or 50) * 2) or 100
        }

        # 1. Save to Vector memory
        incident_id = f"inc_{exp.id}_{sig_hash}"
        vector_service.add_incident(incident_id, signature_text, metadata)

        # 2. Save / update LearnedPattern in Relational DB
        try:
            pattern = db.query(models.LearnedPattern).filter(models.LearnedPattern.root_cause == root_cause).first()
            if pattern:
                pattern.times_encountered += 1
                pattern.last_seen_at = datetime.utcnow()
                if is_success:
                    pattern.success_rate = round((pattern.success_rate * (pattern.times_encountered - 1) + 1.0) / pattern.times_encountered, 2)
            else:
                new_pattern = models.LearnedPattern(
                    signature_hash=sig_hash,
                    title=f"Telemetry Pattern: {root_cause.replace('_', ' ').title()}",
                    root_cause=root_cause,
                    symptoms=[
                        f"P95 Latency elevated to {round(exp.p95_ms or 0, 1)}ms",
                        f"Breaking concurrency at {exp.breaking_point_users or 50} users",
                        f"Observed error rate: {round((exp.error_rate or 0) * 100, 1)}%"
                    ],
                    remediation_strategy=rec_action,
                    success_rate=1.0,
                    times_encountered=1,
                    last_seen_at=datetime.utcnow()
                )
                db.add(new_pattern)
            db.commit()
        except Exception as e:
            db.rollback()

        return True

learner = Learner()

