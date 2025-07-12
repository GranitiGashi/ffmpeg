from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 🔒 VERY simple “database”
VALID_EMAIL = "granit.g4shii@gmail.com"
VALID_PASSWORD = "12345678"

# ── Login form ─────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None}
    )

# ── Form submit ────────────────────────────────────────────────────
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == VALID_EMAIL and password == VALID_PASSWORD:
        # You can store anything JSON‑serialisable in session
        request.session["user"] = {
            "name": username.split("@")[0],
            "email": username,
            "id": 1                                      # fake ID for demo
        }
        return RedirectResponse("/", status_code=303)

    # Wrong creds → show form again with error
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials. Try again."},
        status_code=401
    )

# ── Logout ─────────────────────────────────────────────────────────
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")
