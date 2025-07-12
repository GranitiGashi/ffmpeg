import os, requests, urllib.parse, uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.client_config import get_n8n_webhook_by_email

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

@router.get("/fb/callback")
def fb_callback(code: str, state: str, request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    redirect_uri = f"https://{BASE_DOMAIN}/fb/callback"

    # Step 1: Get short-lived user token
    res = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "client_id": FB_APP_ID,
        "redirect_uri": redirect_uri,
        "client_secret": FB_APP_SECRET,
        "code": code,
    })
    short_token = res.json().get("access_token")

    # Step 2: Get long-lived user token
    res2 = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "fb_exchange_token": short_token,
    })
    long_token = res2.json().get("access_token")

    # Step 3: Get page token
    pages = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
        "access_token": long_token,
    }).json()["data"]
    
    if not pages:
        raise HTTPException(400, "No pages found")

    page_token = pages[0]["access_token"]
    page_id = pages[0]["id"]

    # Step 4: Send to n8n or store here
    email = user["email"]
n8n_url = get_n8n_webhook_by_email(email)

if not n8n_url:
    raise HTTPException(400, f"No webhook configured for {email}")

payload = {
    "page_id": page_id,
    "page_token": page_token,
    "user": user
}

try:
    res = requests.post(n8n_url, json=payload)
    res.raise_for_status()
except requests.RequestException as e:
    print(f"Failed to send to n8n webhook for {email}: {e}")

    # Logout user from Facebook session in browser (prevent sticky login)
    logout_fb = "https://www.facebook.com/logout.php"

    return HTMLResponse(f"""
    <html>
      <head><title>Connected</title></head>
      <body>
        <h2>✅ Facebook connected!</h2>
        <p>Page ID: {page_id}</p>
        <p><a href="/logout">Log out of app</a></p>
        <script>
          setTimeout(() => {{
            window.location = "{logout_fb}";
          }}, 2000);
        </script>
      </body>
    </html>
    """)
