from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
import os, uuid, json, urllib.parse, requests
from dotenv import load_dotenv
from app.supabase_client import upsert_social_record

load_dotenv()
router = APIRouter()

FB_APP_ID = os.getenv("FACEBOOK_APP_ID")
FB_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost:8000")  # e.g. yourdomain.com/api/fb/callback

# STEP 1: Return login URL to frontend
@router.get("/api/fb/login-url")
async def get_fb_login_url(user_id: str):
    state_data = {"user_id": user_id, "nonce": str(uuid.uuid4())}
    state = urllib.parse.quote(json.dumps(state_data))
    redirect_uri = f"https://{BASE_DOMAIN}/api/fb/callback"

    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={FB_APP_ID}&redirect_uri={redirect_uri}"
        f"&state={state}&scope=pages_show_list,pages_manage_posts"
    )
    return JSONResponse({"auth_url": auth_url, "state": state})


# STEP 2: Handle callback and respond to frontend
@router.get("/api/fb/callback")
def fb_callback(code: str = None, state: str = None, error: str = None, error_message: str = None):
    if error:
        return JSONResponse({"error": error_message}, status_code=400)

    try:
        decoded_state = urllib.parse.unquote(state)
        state_data = json.loads(decoded_state)
        user_id = state_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in state")
    except Exception as e:
        return JSONResponse({"error": f"Invalid state: {str(e)}"}, status_code=400)

    redirect_uri = f"https://{BASE_DOMAIN}/api/fb/callback"

    # Step 1: Short-lived token
    token_response = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "client_id": FB_APP_ID,
        "redirect_uri": redirect_uri,
        "client_secret": FB_APP_SECRET,
        "code": code,
    })
    if not token_response.ok:
        return JSONResponse({"error": "Failed to get short-lived token"}, status_code=400)

    short_token = token_response.json().get("access_token")

    # Step 2: Long-lived token
    long_token_response = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "fb_exchange_token": short_token,
    })
    long_token = long_token_response.json().get("access_token")

    # Step 3: Get Pages
    pages_response = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
        "access_token": long_token,
    })
    pages = pages_response.json().get("data", [])

    if not pages:
        return JSONResponse({"error": "No Facebook Pages found"}, status_code=400)

    page = pages[0]
    page_id = page["id"]
    page_token = page["access_token"]

    # Step 4: Get IG Account (optional)
    ig_id = None
    ig_response = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}",
        params={"fields": "instagram_business_account", "access_token": page_token}
    )
    if ig_response.ok:
        ig_data = ig_response.json().get("instagram_business_account", {})
        ig_id = ig_data.get("id")

    # Step 5: Save to Supabase
    upsert_social_record(
        user_id=user_id,
        provider="facebook",
        account_id=page_id,
        access_token=page_token,
        metadata={"page": page},
        token=None  # You can add auth token support here if needed
    )
    if ig_id:
        upsert_social_record(
            user_id=user_id,
            provider="instagram",
            account_id=ig_id,
            access_token=page_token,
            metadata={"linked_fb_page_id": page_id},
            token=None
        )

    return JSONResponse({
        "status": "connected",
        "facebook_id": page_id,
        "instagram_id": ig_id,
        "access_token": page_token,
    })
