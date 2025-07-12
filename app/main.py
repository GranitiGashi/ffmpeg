from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret")  # use a secure key

# Set up Jinja2 templates
templates = Jinja2Templates(directory="./templates")

# Include your routers
app.include_router(auth_router)
app.include_router(fb_router)

# Home route (base domain)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_data = request.session.get("user")
    return templates.TemplateResponse("index.html", {"request": request, "user_data": user_data})

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
