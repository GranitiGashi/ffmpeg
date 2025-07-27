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
from app.video_utils import download_images, generate_cool_video
from app.transitions import get_random_template

# Ensure Supabase client loads
import app.supabase_client as _

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router
from app.tiktok_oauth import router as tiktok_router
from app.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware

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


# Static assets (css / js / images)
app.mount("/static", StaticFiles(directory="static"), name="static")