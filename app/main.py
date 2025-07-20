from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Ensure Supabase client loads
import app.supabase_client as _

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router
from app.tiktok_oauth import router as tiktok_router
from app.routes import api

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="a-very-secure-random-secret-key")  # Change this to a secure key!

templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth_router)
app.include_router(fb_router)
app.include_router(tiktok_router)
app.include_router(api.router)

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

# Static assets (css / js / images)
app.mount("/static", StaticFiles(directory="static"), name="static")