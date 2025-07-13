from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# ensure Supabase client loads
import app.supabase_client as _

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret")   # change this!

templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth_router)
app.include_router(fb_router)

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
        {"request": request, "user_data": user}      # user_data passed to Jinja
    )

# Friendly alias for FB login
@app.get("/connect")
async def connect():
    return RedirectResponse("/fb/login")

# Static assets (css / js / images)
app.mount("/static", StaticFiles(directory="static"), name="static")
