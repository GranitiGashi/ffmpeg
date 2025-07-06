import os
import uuid
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from celery.result import AsyncResult
import requests
from dotenv import load_dotenv
from app.tasks import generate_video_task
from celery_worker import celery_app

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Configuration
FACEBOOK_APP_ID = "1821140208461098"
FACEBOOK_APP_SECRET = "f3d34c01a95cd3f83c5984d93bbaad35"
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"

# Simulated token storage (replace with a database in production)
user_tokens = {}

class VideoRequest(BaseModel):
    image_urls: List[str]

def get_user_token(user_id: str):
    return user_tokens.get(user_id)

# Health Check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Video Generation Endpoints
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

# Authentication Endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: str = "user1"):  # Placeholder user_id
    token = get_user_token(user_id)
    user_data = None
    if token:
        graph_url = "https://graph.facebook.com/v19.0/me"
        params = {"fields": "id,name", "access_token": token}
        response = requests.get(graph_url, params=params)
        user_data = response.json()
    return templates.TemplateResponse("index.html", {"request": request, "user_data": user_data, "user_id": user_id})

@app.get("/connect")
async def connect_social():
    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "pages_show_list,pages_read_engagement,instagram_basic,manage_pages,publish_to_groups,publish_to_pages,instagram_manage_posts",
        "response_type": "code",
    }
    auth_url = f"{AUTH_URL}?{requests.compat.urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/callback")
async def facebook_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    token_params = {
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    response = requests.get(TOKEN_URL, params=token_params)
    token_data = response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    access_token = token_data["access_token"]
    user_id = "user1"  # Replace with real user ID logic (e.g., from session or state parameter)
    user_tokens[user_id] = access_token

    # Fetch user/page ID (App ID in your context might mean user/page ID)
    graph_url = "https://graph.facebook.com/v19.0/me"
    params = {"fields": "id", "access_token": access_token}
    user_response = requests.get(graph_url, params=params)
    user_data = user_response.json()
    user_id = user_data["id"]  # Use actual user ID
    user_tokens[user_id] = access_token  # Update with real ID

    return RedirectResponse(url="/")

@app.post("/post/{user_id}")
async def post_content(user_id: str, token=Depends(get_user_token), content: str = Form(...), platform: str = Form(...)):
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    if platform == "facebook":
        url = "https://graph.facebook.com/v19.0/me/feed"
        params = {"message": content, "access_token": token}
    elif platform == "instagram":
        page_url = "https://graph.facebook.com/v19.0/me/accounts"
        page_response = requests.get(page_url, params={"access_token": token})
        page_data = page_response.json()
        if not page_data.get("data"):
            raise HTTPException(status_code=400, detail="No linked pages found")
        page_id = page_data["data"][0]["id"]
        ig_user_id_url = f"https://graph.facebook.com/v19.0/{page_id}"
        ig_response = requests.get(ig_user_id_url, params={"fields": "instagram_business_account", "access_token": token})
        ig_data = ig_response.json()
        ig_user_id = ig_data.get("instagram_business_account", {}).get("id")
        if not ig_user_id:
            raise HTTPException(status_code=400, detail="No linked Instagram account found")
        url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        params = {
            "access_token": token,
            "caption": content,
            "image_url": "https://example.com/image.jpg"  # Replace with video URL from R2
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid platform")

    response = requests.post(url, data=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Posting failed: {response.text}")
    return {"status": "posted", "platform": platform, "post_id": response.json().get("id")}