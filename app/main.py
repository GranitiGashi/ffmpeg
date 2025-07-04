# FILE: main.py (updated with Celery + R2)
import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from celery.result import AsyncResult
from app.tasks import generate_video_task
from celery_worker import celery_app

app = FastAPI()

class VideoRequest(BaseModel):
    image_urls: List[str]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate-video/")
def generate_video_endpoint(request: VideoRequest):
    task = generate_video_task.delay(request.image_urls)
    return {
        "status": "processing",
        "task_id": task.id
    }

@app.get("/generate-video/status/{task_id}")
def get_job_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "STARTED":
        return {"status": "started"}
    elif result.state == "SUCCESS":
        return {
            "status": "completed",
            "video_url": result.result.get("video_url")
        }
    elif result.state == "FAILURE":
        return {
            "status": "failed",
            "error": str(result.result)
        }
    else:
        return {"status": result.state}
