import bcrypt
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.supabase_client import (
    supabase, create_supabase_user, hash_pw, verify_password,
    get_user_record, insert_user_record
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

##############################################################################
# Sign-up (admin only) – optional
##############################################################################
@router.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        uid = create_supabase_user(email, password)
        insert_user_record(uid, email, hash_pw(password))
        return RedirectResponse("/login", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("signup.html", {"request": request, "error": str(e)}, status_code=400)

##############################################################################
# Login
##############################################################################
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    record = get_user_record(email)
    if not record:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User not found"}, status_code=401)
    if not verify_password(password, record["password_hash"].encode()):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    try:
        session = supabase.auth.sign_in_with_password({"email": email, "password": password})
        request.session["user"] = {
            "id": record["id"],
            "email": email,
            "jwt": session.session.access_token
        }
        print(f"Login successful, session set: {request.session['user']}")  # Debug log
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Authentication failed: {str(e)}"}, status_code=401)
##############################################################################
# Logout
##############################################################################
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")