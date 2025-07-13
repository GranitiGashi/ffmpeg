import os, requests, urllib.parse, uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.client_config import get_n8n_webhook_by_email
from app.supabase_client import upsert_social_record

load_dotenv()

router = APIRouter()

FB_APP_ID = os.getenv("FACEBOOK_APP_ID")
FB_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
BASE_DOMAIN = os.getenv("BASE_DOMAIN")

@router.get("/fb/login")
def fb_login(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login")

    state = f"{request.session['user']}:{uuid.uuid4()}"
    redirect_uri = f"https://{BASE_DOMAIN}/fb/callback"
    url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={FB_APP_ID}&redirect_uri={redirect_uri}"
        f"&state={state}&scope=pages_show_list,pages_manage_posts"
    )
    return RedirectResponse(url)

from app.client_config import get_n8n_webhook_by_email

@router.get("/fb/callback")
def fb_callback(
    request: Request, code: str | None = None,
    state: str | None = None, error: str | None = None,
    error_message: str | None = None
):
    if error:
        return HTMLResponse(f"<h3 style='color:red;'>Facebook error: {error_message}</h3>")

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    redirect_uri = f"https://{BASE_DOMAIN}/fb/callback"

    # 1) short token
    short = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "client_id": FB_APP_ID, "redirect_uri": redirect_uri,
        "client_secret": FB_APP_SECRET, "code": code,
    }).json().get("access_token")

    # 2) long token
    long_tok = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": FB_APP_ID, "client_secret": FB_APP_SECRET,
        "fb_exchange_token": short,
    }).json().get("access_token")

    # 3) Get Pages
    pages = requests.get("https://graph.facebook.com/v19.0/me/accounts",
                         params={"access_token": long_tok}).json().get("data", [])
    if not pages:
        raise HTTPException(400, "No FB pages found")

    page = pages[0]
    page_id, page_token = page["id"], page["access_token"]

    # 4) Instagram business ID
    ig_id = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}",
        params={"fields": "instagram_business_account", "access_token": page_token}
    ).json().get("instagram_business_account", {}).get("id")

    # 5) Save in Supabase
    upsert_social_record(user["supabase_uid"], page_id, page_token, ig_id)

    return HTMLResponse(f"""
    <h2>✅ Connected!</h2>
    <p>FB Page ID: {page_id}</p>
    <p>IG ID: {ig_id or '—'}</p>
    <a href='/'>Back to dashboard</a>
    """)