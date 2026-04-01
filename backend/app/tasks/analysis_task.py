import json
import os
# [MOCK] from celery import Celery

# celery_app = Celery("truthlens", broker=os.getenv("CELERY_BROKER_URL"), backend=os.getenv("CELERY_RESULT_BACKEND"))

def update_progress(job_id: str, step_name: str, percent: int):
    # sets Redis key "job:{job_id}:progress" as JSON
    # Frontend polls /api/v1/analyze/status/{job_id} which reads this Redis key
    
    # [MOCK REDIS CALL]
    # redis_client.set(f"job:{job_id}:progress", json.dumps({"step": step_name, "percent": percent}))
    pass

def persist_result_to_db(job_id: str, fusion_result, risk_level, explanation):
    # [MOCK DATABASE CALL]
    pass

import shutil
import logging

def run_modality_safe(func, *args):
    try:
        # Check DEMO_MODE inside function if needed, here we just run it
        if os.getenv("DEMO_MODE", "false").lower() == "true":
            return {"fake_probability": 0.5, "flags": ["demo_mode"]}
        return func(*args)
    except Exception as e:
        logging.error(f"Modality pipeline failed: {e}")
        return {"fake_probability": 0.5, "flags": []}

def run_visual_pipeline(media_bundle): return {"fake_probability": 0.5, "flags": []}
def run_audio_pipeline(media_bundle): return {"fake_probability": 0.2, "flags": []}
def run_text_pipeline(media_bundle): return {"fake_probability": 0.1, "flags": []}
def run_crossmodal_pipeline(media_bundle, visual_result, audio_result): return {"fake_probability": 0.3, "flags": []}

# @celery_app.task(bind=True, max_retries=2)
def run_analysis_pipeline(self, job_id: str):
    
    update_progress(job_id, "ingestion", 5)
    media_bundle = {} # MOCK
    
    update_progress(job_id, "visual_analysis", 20)
    visual_result = run_modality_safe(run_visual_pipeline, media_bundle)
    
    update_progress(job_id, "audio_forensics", 45)
    audio_result = run_modality_safe(run_audio_pipeline, media_bundle)
    
    update_progress(job_id, "text_verification", 65)
    text_result = run_modality_safe(run_text_pipeline, media_bundle)
    
    update_progress(job_id, "crossmodal_alignment", 80)
    crossmodal_result = run_modality_safe(run_crossmodal_pipeline, media_bundle, visual_result, audio_result)
    
    update_progress(job_id, "score_fusion", 90)
    class MockFusion:
        authenticity_score = 85.0
    fusion_result = MockFusion()
    
    risk_level = "authentic"
    explanation = "Mock explanation."
    
    update_progress(job_id, "complete", 100)
    persist_result_to_db(job_id, fusion_result, risk_level, explanation)
    
    # Media cleanup
    shutil.rmtree(f"/tmp/{job_id}", ignore_errors=True)
    # [MOCK] s3_client.delete_extracted_artifacts(job_id) # delete frames/audio.wav from s3
    
    return "Pipeline Complete"
