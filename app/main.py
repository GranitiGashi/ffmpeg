import os
import uuid
import random
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.responses import FileResponse

from generate import download_images
from video_utils import generate_cool_video

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

        image_paths = download_images(request.image_urls, folder=tmp_dir)
        generate_cool_video(image_paths, output=output_path, transitions=transitions)

        return {
            "status": "success",
            "video_path": f"/videos/{job_id}/output.mp4",
            "template_used": chosen
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{job_id}/output.mp4")
def get_video(job_id: str):
    file_path = f"tmp/{job_id}/output.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")