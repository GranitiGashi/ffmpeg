import os
import subprocess
import requests
import random
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI()

class VideoRequest(BaseModel):
    image_urls: List[str]

def download_images(urls, folder):
    os.makedirs(folder, exist_ok=True)
    paths = []
    for i, url in enumerate(urls):
        filename = os.path.join(folder, f'image{i+1}.jpg')
        resp = requests.get(url)
        resp.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(resp.content)
        paths.append(filename)
    return paths

def generate_cool_video(image_paths, output='output.mp4', transitions=None):
    if len(image_paths) != 10:
        raise ValueError("You must provide exactly 10 images.")

    duration = 3
    transition = 1
    input_args = []

    for img in image_paths:
        input_args.extend(["-loop", "1", "-t", str(duration), "-i", img])

    filters = []
    for i in range(len(image_paths)):
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuva420p,setsar=1[v{i}]"
        )

    if transitions is None:
        transitions = ["fade"] * (len(image_paths) - 1)

    for i in range(len(image_paths) - 1):
        trans = transitions[i % len(transitions)]
        offset = (duration - transition) * i + duration - transition
        if i == 0:
            filters.append(f"[v0][v1]xfade=transition={trans}:duration={transition}:offset={offset}[x0]")
        else:
            filters.append(f"[x{i-1}][v{i+1}]xfade=transition={trans}:duration={transition}:offset={offset}[x{i}]")

    last_output = f"[x{len(image_paths) - 2}]"
    filter_chain = ";".join(filters) + f";{last_output}format=yuv420p[v]"

    total_duration = duration + (duration - transition) * (len(image_paths) - 2)

    cmd = [
        "ffmpeg",
        "-y",
        *input_args,
        "-filter_complex", filter_chain,
        "-map", "[v]",
        "-t", str(total_duration),
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("FFmpeg failed")

@app.post("/generate-video/")
def generate_video_endpoint(request: VideoRequest):
    job_id = str(uuid.uuid4())
    tmp_dir = f"tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    output_path = os.path.join(tmp_dir, "output.mp4")

    try:
        # Transition templates
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
    return FastAPI.responses.FileResponse(file_path, media_type="video/mp4", filename="output.mp4")
