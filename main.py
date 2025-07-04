# app/main.py
import os
import uuid
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from app.video_utils import download_images, generate_cool_video
from app.transitions import get_random_template

app = FastAPI()

class VideoRequest(BaseModel):
    image_urls: List[str]

@app.post("/generate-video/")
def generate_video_endpoint(request: VideoRequest):
    job_id = str(uuid.uuid4())
    tmp_dir = f"tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    output_path = os.path.join(tmp_dir, "output.mp4")

    try:
        transitions, template_name = get_random_template()
        image_paths = download_images(request.image_urls, folder=tmp_dir)
        generate_cool_video(image_paths, output=output_path, transitions=transitions)

        return {
            "status": "success",
            "video_path": f"/videos/{job_id}/output.mp4",
            "template_used": template_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{job_id}/output.mp4")
def get_video(job_id: str):
    file_path = f"tmp/{job_id}/output.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")
