import os
import uuid
import shutil
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from typing import List
from app.video_utils import generate_cool_video
from app.generate import download_images
from transitions import get_random_template

# Ensure Supabase client loads
import app.supabase_client as _

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router
from app.tiktok_oauth import router as tiktok_router
from app.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware

from app.tasks import generate_video_task

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://www.scriptiflow.com/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="a-very-secure-random-secret-key")  # Change this to a secure key!

templates = Jinja2Templates(directory="app/templates")

class VideoRequest(BaseModel):
    image_urls: List[str]

# Routers
app.include_router(auth_router)
app.include_router(fb_router)
app.include_router(tiktok_router)
app.include_router(api_router)

# Health check (for Render)
@app.get("/health")
def health():
    return {"status": "ok"}

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user_data": user}
    )

# Friendly aliases
@app.get("/connect")
async def connect():
    return RedirectResponse("/fb/login")

@app.get("/connect/tiktok")
async def connect_tiktok():
    return RedirectResponse("/tiktok/login")


@app.post("/generate-video/")
async def generate_video_endpoint(request: VideoRequest):
    job_id = str(uuid.uuid4())
    # Pass only image_urls to Celery task; job_id generated inside task for uniqueness
    task = generate_video_task.delay(request.image_urls)
    return {
        "status": "submitted",
        "task_id": task.id,
        "job_id": job_id  # Note: job_id generated here is not linked to the task's job_id in task
    }

# Endpoint to serve generated video from local storage (optional if you rely on R2 URL)
@app.get("/videos/{job_id}/output.mp4")
def get_video(job_id: str):
    file_path = f"tmp/{job_id}/output.mp4"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")


# Static assets (css / js / images)
app.mount("/static", StaticFiles(directory="static"), name="static")