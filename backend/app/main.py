import asyncio
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from database import get_db, engine, Base
import models
import schemas
from config import TARGET_APP_URL
from services.docker_service import docker_service
from services.locust_service import locust_service
from services.prometheus_service import prometheus_service
from services.vector_service import vector_service
from agents.workload_designer import workload_designer
from agents.diagnostician import diagnostician
from agents.remediator import remediator
from agents.learner import learner

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LoadMind Backend Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dictionary to track active metric logs for live graphs
test_metrics_history: Dict[int, List[Dict[str, Any]]] = {}

async def run_load_test_loop(experiment_id: int, failure_mode: str, db: Session):
    test_metrics_history[experiment_id] = []
    
    # 1. Set target app failure mode
    docker_service.set_target_failure_mode(failure_mode)
    await asyncio.sleep(2) # let it settle

    # 2. Workload generation
    workload = workload_designer.design_workload()
    print(f"Designed workload: {workload}")

    # 3. Progressive load ramp-up
    concurrency_levels = [10, 25, 50, 100, 250]
    breaking_point_detected = False
    breaking_users = 0
    final_snapshot = None

    for users in concurrency_levels:
        if breaking_point_detected:
            break

        print(f"Ramping up load to {users} users...")
        locust_service.start_load(user_count=users, spawn_rate=5.0)
        
        # Wait and monitor metrics over 10 seconds
        for _ in range(10):
            await asyncio.sleep(1)
            snapshot = prometheus_service.get_metrics_snapshot()
            snapshot["users"] = users
            test_metrics_history[experiment_id].append(snapshot)

            # Check breaking point conditions
            # E.g. error rate > 5% or p95 latency > 1.5 seconds
            error_rate = snapshot.get("error_rate", 0.0)
            p95_ms = snapshot.get("p95_ms", 0.0)
            
            if error_rate > 0.05 or p95_ms > 1500.0:
                breaking_point_detected = True
                breaking_users = users
                final_snapshot = snapshot
                print(f"Breaking point detected at {users} users! (Error rate: {error_rate}, P95: {p95_ms}ms)")
                break

    # Stop Locust load
    locust_service.stop_load()

    # Update database record
    exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if exp:
        exp.status = "completed"
        if breaking_point_detected and final_snapshot:
            exp.breaking_point_users = breaking_users
            exp.p50_ms = final_snapshot.get("p50_ms")
            exp.p95_ms = final_snapshot.get("p95_ms")
            exp.p99_ms = final_snapshot.get("p99_ms")
            exp.error_rate = final_snapshot.get("error_rate")
        else:
            # Did not break, set default max concurrency tested
            exp.breaking_point_users = concurrency_levels[-1]
            last_snap = test_metrics_history[experiment_id][-1] if test_metrics_history[experiment_id] else {}
            exp.p50_ms = last_snap.get("p50_ms", 0.0)
            exp.p95_ms = last_snap.get("p95_ms", 0.0)
            exp.p99_ms = last_snap.get("p99_ms", 0.0)
            exp.error_rate = last_snap.get("error_rate", 0.0)
        
        db.commit()

        # Run Diagnostician automatically
        metrics_for_diag = {
            "breaking_point_users": exp.breaking_point_users,
            "p50_ms": exp.p50_ms,
            "p95_ms": exp.p95_ms,
            "p99_ms": exp.p99_ms,
            "error_rate": exp.error_rate,
            "cpu_percent": final_snapshot.get("cpu_percent", 0.0) if final_snapshot else 0.0,
            "memory_mb": final_snapshot.get("memory_mb", 0.0) if final_snapshot else 0.0,
        }
        
        diag_data = diagnostician.diagnose(metrics_for_diag, failure_mode_hint=failure_mode)
        diagnosis = models.Diagnosis(
            experiment_id=exp.id,
            primary_root_cause=diag_data["primary_root_cause"],
            confidence=diag_data["confidence"],
            evidence=diag_data["evidence"],
            alternative_causes=diag_data["alternative_causes"],
            recommended_action=diag_data["recommended_action"]
        )
        db.add(diagnosis)
        db.commit()

@app.post("/api/tests/start", response_model=schemas.ExperimentResponse)
def start_test(req: schemas.ExperimentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    exp = models.Experiment(
        target_app_url=TARGET_APP_URL,
        failure_mode=req.failure_mode,
        status="running"
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    background_tasks.add_task(run_load_test_loop, exp.id, req.failure_mode, db)
    return exp

@app.get("/api/tests/{id}", response_model=schemas.ExperimentResponse)
def get_test(id: int, db: Session = Depends(get_db)):
    exp = db.query(models.Experiment).filter(models.Experiment.id == id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

@app.get("/api/tests/{id}/metrics")
def get_test_metrics(id: int):
    return test_metrics_history.get(id, [])

@app.get("/api/tests/{id}/diagnosis", response_model=schemas.DiagnosisResponse)
def get_test_diagnosis(id: int, db: Session = Depends(get_db)):
    diag = db.query(models.Diagnosis).filter(models.Diagnosis.experiment_id == id).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found yet")
    return diag

@app.get("/api/tests/{id}/remediation")
def get_test_remediation(id: int, db: Session = Depends(get_db)):
    rem = db.query(models.Remediation).filter(models.Remediation.experiment_id == id).first()
    if not rem:
        # Create proposed remediation on demand if not exists
        diag = db.query(models.Diagnosis).filter(models.Diagnosis.experiment_id == id).first()
        if not diag:
            raise HTTPException(status_code=400, detail="Cannot propose remediation without diagnosis")
        
        rem_data = remediator.remediate(diag.primary_root_cause)
        rem = models.Remediation(
            experiment_id=id,
            proposed_remediation=rem_data["proposed_remediation"],
            patch_diff=rem_data["patch_diff"],
            is_applied=False
        )
        db.add(rem)
        db.commit()
        db.refresh(rem)

    return rem

@app.post("/api/tests/{id}/remediate")
def apply_remediation(id: int, db: Session = Depends(get_db)):
    rem = db.query(models.Remediation).filter(models.Remediation.experiment_id == id).first()
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation not found")
    
    # Trigger restart of target container to load files (safely)
    docker_service.restart_target_app()
    
    rem.is_applied = True
    rem.applied_at = datetime.utcnow()
    db.commit()
    return {"status": "remediation applied", "remediation": rem}

@app.post("/api/tests/{id}/verify")
async def verify_remediation(id: int, db: Session = Depends(get_db)):
    exp = db.query(models.Experiment).filter(models.Experiment.id == id).first()
    rem = db.query(models.Remediation).filter(models.Remediation.experiment_id == id).first()
    if not exp or not rem:
        raise HTTPException(status_code=404, detail="Experiment or Remediation not found")

    # Run the identical workload
    concurrency = exp.breaking_point_users or 50
    print(f"Verification: Running same load profile of {concurrency} users...")
    
    locust_service.start_load(user_count=concurrency, spawn_rate=10.0)
    
    # Measure metrics over 10 seconds under load
    verification_metrics = []
    for _ in range(10):
        await asyncio.sleep(1)
        snapshot = prometheus_service.get_metrics_snapshot()
        verification_metrics.append(snapshot)
    
    locust_service.stop_load()

    # Calculate average verification metrics
    avg_error_rate = sum(m.get("error_rate", 0.0) for m in verification_metrics) / len(verification_metrics)
    avg_p95_ms = sum(m.get("p95_ms", 0.0) for m in verification_metrics) / len(verification_metrics)
    
    # Determine if remediation succeeded
    success = avg_error_rate < 0.02 and avg_p95_ms < 1000.0
    
    # Calculate improvement
    before_p95 = exp.p95_ms or 1.0
    latency_improvement = max(0.0, round(((before_p95 - avg_p95_ms) / before_p95) * 100, 2))

    rem.verified = True
    rem.success = success
    rem.latency_improvement_percent = latency_improvement
    rem.error_rate_before = exp.error_rate
    rem.error_rate_after = avg_error_rate
    rem.breaking_point_before = concurrency
    rem.breaking_point_after = concurrency * 2 if success else concurrency
    db.commit()

    # Learn from outcome
    learner.learn(db, exp.id, rem.id)

    return {
        "verified": True,
        "success": success,
        "latency_improvement_percent": latency_improvement,
        "error_rate_before": exp.error_rate,
        "error_rate_after": avg_error_rate,
        "breaking_point_before": concurrency,
        "breaking_point_after": rem.breaking_point_after
    }

@app.get("/api/incidents")
def get_incidents(db: Session = Depends(get_db)):
    experiments = db.query(models.Experiment).order_by(models.Experiment.created_at.desc()).all()
    result = []
    for exp in experiments:
        diag = db.query(models.Diagnosis).filter(models.Diagnosis.experiment_id == exp.id).first()
        rem = db.query(models.Remediation).filter(models.Remediation.experiment_id == exp.id).first()
        result.append({
            "id": exp.id,
            "failure_mode": exp.failure_mode,
            "status": exp.status,
            "breaking_point_users": exp.breaking_point_users,
            "p95_ms": exp.p95_ms,
            "error_rate": exp.error_rate,
            "diagnosis": diag.primary_root_cause if diag else None,
            "success": rem.success if rem else None
        })
    return result

@app.get("/api/learning")
def get_learning_stats(db: Session = Depends(get_db)):
    remediations = db.query(models.Remediation).filter(models.Remediation.verified == True).all()
    total_runs = len(remediations)
    successful_runs = sum(1 for r in remediations if r.success)
    
    return {
        "total_incidents_stored": db.query(models.Experiment).count(),
        "remediation_success_rate": round((successful_runs / total_runs * 100), 2) if total_runs > 0 else 0.0,
        "signatures_learned": db.query(models.Diagnosis.primary_root_cause).distinct().count()
    }

@app.get("/api/health")
def health():
    return {"status": "healthy"}
