import os
import requests
import urllib.parse
import uuid
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.supabase_client import upsert_social_record

load_dotenv()
router = APIRouter()

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
BASE_DOMAIN = os.getenv("BASE_DOMAIN")
SCOPES = "user.info.basic,video.upload,video.publish"

@router.get("/tiktok/login")
def tiktok_login(request: Request):
    user = request.session.get("user")
    if not user or "id" not in user:
        return RedirectResponse("/login")
    state = f"{json.dumps({'id': user['id']})}:{uuid.uuid4()}"
    redirect_uri = f"https://{BASE_DOMAIN}/auth/callback"

    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    url = "https://www.tiktok.com/v2/auth/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)

@router.get("/tiktok/callback")
def tiktok_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None, error_description: str | None = None):
    if error:
        return HTMLResponse(f"<h3 style='color:red;'>TikTok error: {error_description}</h3>")

    if not state:
        return RedirectResponse("/login")
    try:
        state_data, _ = state.split(':', 1)
        user = json.loads(state_data)
        if not user or "id" not in user:
            raise ValueError("Invalid state data")
    except (ValueError, json.JSONDecodeError):
        return RedirectResponse("/login")

    redirect_uri = f"https://{BASE_DOMAIN}/auth/callback"

    # Exchange code for token
    response = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if not response.ok:
        raise HTTPException(400, "Failed to get TikTok access token")
    token_resp = response.json()

    if "data" not in token_resp or "access_token" not in token_resp["data"]:
        return HTMLResponse(f"<h3 style='color:red;'>Failed to get TikTok access token</h3><pre>{token_resp}</pre>")

    data = token_resp["data"]
    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")
    open_id = data["open_id"]

    # Save TikTok account
    upsert_social_record(
        user_id=user["id"],
        provider="tiktok",
        account_id=open_id,
        access_token=access_token,
        refresh_token=refresh_token,
        metadata=data,
        token=request.session.get("jwt")
    )

    return HTMLResponse(f"""
        <h2>✅ TikTok Connected!</h2>
        <p>TikTok Open ID: {open_id}</p>
        <a href='/'>Back to dashboard</a>
    """)