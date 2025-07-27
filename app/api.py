from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from app.supabase_client import supabase
from app.supabase_client import (
    create_supabase_user,
    hash_pw,
    insert_user_record,
    verify_password,
    get_user_record,
    get_social_accounts,
)
import logging

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register_user(data: RegisterRequest):
    existing = get_user_record(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    uid = create_supabase_user(data.email, data.password)
    hashed = hash_pw(data.password)
    insert_user_record(uid, data.email, hashed)
    return {"message": "User registered", "uid": uid}

@router.post("/login")
def login_user(data: LoginRequest):
    user = get_user_record(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {"message": "Login successful", "user_id": user["id"]}

@router.get("/api/social-accounts")
async def get_social_accounts(request: Request):
    print("Session:", request.session)
    user = request.session.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = user["id"]
        response = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
        print("Supabase response:", response)
        return {"accounts": response.data}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.get("/api/social-accounts-by-email")
async def get_social_accounts_by_email(email: str = Query(..., description="User email to lookup social accounts for")):
    logging.debug(f"Request received for email: {email}")
    
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    try:
        # Fetch user by email
        users_response = supabase.table("users_app").select("id").eq("email", email).execute()
        users = users_response.data

        if not users:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = users[0]["id"]
        logging.debug(f"Found user_id: {user_id}")

        # Fetch related social accounts
        accounts_response = supabase.table("social_accounts").select("provider, account_id, access_token").eq("user_id", user_id).execute()
        accounts = accounts_response.data

        if not accounts:
            raise HTTPException(status_code=404, detail="No social accounts found for this user")

        fb_account = next((acc for acc in accounts if acc["provider"] == "facebook"), None)
        ig_account = next((acc for acc in accounts if acc["provider"] == "instagram"), None)

        return {
            "email": email,
            "facebook_id": fb_account["account_id"] if fb_account else None,
            "instagram_id": ig_account["account_id"] if ig_account else None,
            "access_token_fb": fb_account["access_token"] if fb_account else None
        }

    except Exception as e:
        logging.exception("Unhandled exception occurred")
        raise HTTPException(status_code=500, detail="Internal Server Error")