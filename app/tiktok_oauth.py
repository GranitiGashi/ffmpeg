import os, requests, urllib.parse, uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.supabase_client import upsert_social_record

load_dotenv()

router = APIRouter()

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
BASE_DOMAIN = os.getenv("BASE_DOMAIN")  # Optional, fallback to request.base_url

SCOPES = "user.info.basic,video.upload,video.publish"

@router.get("/tiktok/login")
def tiktok_login(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login")

    state = f"{request.session['user']}:{uuid.uuid4()}"
    redirect_uri = f"https://{BASE_DOMAIN}/tiktok/callback"  # ✅ No state here!

    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": redirect_uri,
        "state": state,  # ✅ Pass it separately
        "optional_scope": "",
    }

    url = "https://www.tiktok.com/auth/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/tiktok/callback")
def tiktok_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None
):
    if error:
        return HTMLResponse(f"<h3 style='color:red;'>TikTok error: {error_description}</h3>")

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    redirect_uri = f"{request.base_url}tiktok/callback"

    # Exchange code for access token
    token_url = "https://open-api.tiktok.com/oauth/access_token/"
    payload = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(token_url, json=payload, headers=headers)
    token_resp = response.json()

    if "data" not in token_resp or "access_token" not in token_resp["data"]:
        return HTMLResponse(f"""
            <h3 style='color:red;'>Failed to get TikTok access token</h3>
            <pre>{token_resp}</pre>
        """)

    data = token_resp["data"]
    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")
    open_id = data["open_id"]

    # Save in Supabase
    upsert_social_record(
        uid=user["supabase_uid"],
        tiktok_user_id=open_id,
        tiktok_access_token=access_token,
        tiktok_refresh_token=refresh_token
    )

    return HTMLResponse(f"""
        <h2>✅ TikTok Connected!</h2>
        <p>TikTok Open ID: {open_id}</p>
        <a href='/'>Back to dashboard</a>
    """)
