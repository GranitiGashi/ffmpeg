import os
import requests
import uuid
import json
import urllib.parse
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.supabase_client import upsert_social_record

load_dotenv()
router = APIRouter()

FB_APP_ID = os.getenv("FACEBOOK_APP_ID")
FB_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost:8000")  # Default for local testing

@router.get("/fb/login")
def fb_login(request: Request):
    user = request.session.get("user")
    if not user or "id" not in user:
        return RedirectResponse("/login")
    
    # Generate a secure state with user ID and random nonce
    state_data = {"user_id": user["id"], "nonce": str(uuid.uuid4())}
    state = urllib.parse.quote(json.dumps(state_data))
    request.session["fb_state"] = state  # Store encoded state in session
    print(f"Generated state: {state}")  # Debug log

    redirect_uri = f"https://{BASE_DOMAIN}/fb/callback"
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={FB_APP_ID}&redirect_uri={redirect_uri}"
        f"&state={state}&scope=pages_show_list,pages_manage_posts"
    )
    return RedirectResponse(auth_url)

@router.get("/fb/callback")
def fb_callback(request: Request, code: str = None, state: str = None, error: str = None, error_message: str = None):
    print(f"Callback params: code={code}, state={state}, error={error}, error_message={error_message}")  # Debug log
    
    if error:
        return HTMLResponse(f"<h3 style='color:red'>Facebook error: {error_message}</h3>")
    
    expected_state = request.session.get("fb_state")
    if not state or not expected_state:
        print(f"State missing: received {state}, expected {expected_state}")  # Debug log
        return RedirectResponse("/login?error=state_missing")
    
    # Decode expected_state for comparison with unencoded state from Facebook
    expected_state_decoded = urllib.parse.unquote(expected_state)
    if state != expected_state_decoded:
        print(f"State mismatch: received {state}, expected {expected_state_decoded}")  # Debug log
        return RedirectResponse("/login?error=state_mismatch")

    try:
        # Decode and parse the state
        decoded_state = urllib.parse.unquote(state)
        print(f"Decoded state: {decoded_state}")  # Debug log
        state_data = json.loads(decoded_state)
        user_id = state_data.get("user_id")
        if not user_id:
            raise ValueError("Invalid state: missing user_id")
        print(f"Parsed user_id: {user_id}")  # Debug log
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"State parsing error: {str(e)}")  # Debug log
        return RedirectResponse("/login?error=invalid_state")

    redirect_uri = f"https://{BASE_DOMAIN}/fb/callback"

    # 1) Get short-lived token
    token_response = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "client_id": FB_APP_ID,
        "redirect_uri": redirect_uri,
        "client_secret": FB_APP_SECRET,
        "code": code,
    })
    if not token_response.ok:
        raise HTTPException(status_code=400, detail="Failed to get short-lived token")
    short_token = token_response.json().get("access_token")
    if not short_token:
        raise HTTPException(status_code=400, detail="No short-lived token received")

    # 2) Exchange for long-lived token
    long_token_response = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "fb_exchange_token": short_token,
    })
    if not long_token_response.ok:
        raise HTTPException(status_code=400, detail="Failed to exchange token")
    long_token = long_token_response.json().get("access_token")
    if not long_token:
        raise HTTPException(status_code=400, detail="No long-lived token received")

    # 3) Get user pages
    pages_response = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
        "access_token": long_token,
    })
    if not pages_response.ok:
        raise HTTPException(status_code=400, detail="Failed to fetch pages")
    pages = pages_response.json().get("data", [])
    if not pages:
        raise HTTPException(status_code=400, detail="No FB pages found")

    page = pages[0]
    page_id, page_token = page["id"], page["access_token"]

    # 4) Get Instagram business account (optional)
    ig_id = None
    ig_response = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}",
        params={"fields": "instagram_business_account", "access_token": page_token}
    )
    if ig_response.ok:
        ig_data = ig_response.json().get("instagram_business_account", {})
        ig_id = ig_data.get("id")

    # 5) Save FB Page
    upsert_social_record(
        user_id=user_id,
        provider="facebook",
        account_id=page_id,
        access_token=page_token,
        metadata={"page": page},
        token=request.session.get("jwt")
    )

    # 6) Save IG Account (if exists)
    if ig_id:
        upsert_social_record(
            user_id=user_id,
            provider="instagram",
            account_id=ig_id,
            access_token=page_token,
            metadata={"linked_fb_page_id": page_id},
            token=request.session.get("jwt")
        )

    # Clear the state after successful use
    request.session.pop("fb_state", None)

    return HTMLResponse(f"""
    <h2>✅ Connected!</h2>
    <p>FB Page ID: {page_id}</p>
    <p>IG ID: {ig_id or '—'}</p>
    <a href='/'>Back to dashboard</a>
    """)