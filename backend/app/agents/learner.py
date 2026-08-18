from sqlalchemy.orm import Session
import models
from services.vector_service import vector_service

class Learner:
    def learn(self, db: Session, experiment_id: int, remediation_id: int):
        # 1. Retrieve experiment and remediation from relational database
        exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
        rem = db.query(models.Remediation).filter(models.Remediation.id == remediation_id).first()
        diag = db.query(models.Diagnosis).filter(models.Diagnosis.experiment_id == experiment_id).first()
        
        if not exp or not rem or not diag:
            print("Required record not found in database, skipping learning step")
            return False

        # 2. Construct failure signature text
        signature_text = f"concurrency: {exp.breaking_point_users}, cpu: {exp.p50_ms}ms, error_rate: {exp.error_rate}, root_cause: {diag.primary_root_cause}"
        
        # 3. Create metadata
        metadata = {
            "experiment_id": exp.id,
            "failure_mode": exp.failure_mode,
            "primary_root_cause": diag.primary_root_cause,
            "recommended_action": diag.recommended_action,
            "success": rem.success or False,
            "breaking_point_before": rem.breaking_point_before or 0,
            "breaking_point_after": rem.breaking_point_after or 0
        }

        # 4. Save to ChromaDB vector memory
        incident_id = f"incident_{exp.id}"
        success = vector_service.add_incident(incident_id, signature_text, metadata)
        return success

learner = Learner()
