import os
import uuid
import random
import shutil
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.responses import FileResponse

from app.generate import download_images
from app.video_utils import generate_cool_video

app = FastAPI()

# In-memory job store (for demonstration purposes)
jobs: Dict[str, Dict[str, Optional[str]]] = {}

class VideoRequest(BaseModel):
    image_urls: List[str]

def cleanup_tmp_folder(job_id: str):
    folder = f"tmp/{job_id}"
    if os.path.exists(folder):
        shutil.rmtree(folder)

def process_video_job(image_urls: List[str], tmp_dir: str, job_id: str):
    output_path = os.path.join(tmp_dir, "output.mp4")
    try:
        transition_templates = {
            "classic": ["fade"] * 9,
            "slide": ["slideleft", "slideright", "slideup", "slidedown", "slideleft", "slideright", "slideup", "slidedown", "slideleft"],
            "mix": ["fade", "slideleft", "circlecrop", "rectcrop", "distance", "slideup", "slidedown", "smoothleft", "slideright"],
            "random": random.sample([
                "fade", "slideleft", "slideright", "circlecrop", "rectcrop",
                "distance", "slideup", "slidedown", "smoothleft"
            ], 9)
        }

        chosen = random.choice(list(transition_templates.keys()))
        transitions = transition_templates[chosen]

        image_paths = download_images(image_urls, folder=tmp_dir)
        generate_cool_video(image_paths, output=output_path, transitions=transitions)

        jobs[job_id] = {
            "status": "completed",
            "video_path": f"/videos/{job_id}/output.mp4",
            "template_used": chosen
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "video_path": None
        }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate-video/")
def generate_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    tmp_dir = f"tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)

    # Save initial job status
    jobs[job_id] = {
        "status": "processing",
        "video_path": None,
        "template_used": None
    }

    # Start processing in background
    background_tasks.add_task(process_video_job, request.image_urls, tmp_dir, job_id)

    return {"job_id": job_id, "status": "processing"}

@app.get("/generate-video/status/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/videos/{job_id}/output.mp4")
def get_video(job_id: str, background_tasks: BackgroundTasks):
    file_path = f"tmp/{job_id}/output.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    # Schedule cleanup after serving the file
    background_tasks.add_task(cleanup_tmp_folder, job_id)

    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")
