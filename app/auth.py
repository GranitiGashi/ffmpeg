from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from app.supabase_client import (
    supabase, create_supabase_user, hash_pw,
    get_user_record, insert_user_record, verify_password
)

router = APIRouter()


##############################################################################
# Models
##############################################################################

class SignUpPayload(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: str
    role: str = "user"  # Default role if not specified
    permissions: dict = {}

class LoginPayload(BaseModel):
    email: str
    password: str

##############################################################################
# Signup (Admin Only)
##############################################################################

@router.post("/api/signup")
async def signup(payload: SignUpPayload, request: Request):
    user_session = request.session.get("user")

    if not user_session or user_session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can register new users")

    try:
        # Create Supabase user
        uid = create_supabase_user(payload.email, payload.password)

        # Insert custom user record into your table
        insert_user_record(
            uid,
            email=payload.email,
            password_hash=hash_pw(payload.password),
            full_name=payload.full_name,
            company_name=payload.company_name,
            role=payload.role,
            permissions=payload.permissions
        )

        return {"status": "success", "message": "Account created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


##############################################################################
# Login
##############################################################################

@router.post("/api/login")
async def login(payload: LoginPayload, request: Request):
    record = get_user_record(payload.email)

    if not record or not verify_password(payload.password, record["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Login with Supabase auth
    session = supabase.auth.sign_in_with_password({
        "email": payload.email,
        "password": payload.password
    })

    jwt_expires_at = session.session.expires_at

    # Extract role
    role = record.get("role", "user")

    request.session["user"] = {
        "id": record["id"],
        "email": payload.email,
        "jwt": session.session.access_token,
        "expires_at": jwt_expires_at,
        "role": role
    }

    return {
        "status": "success",
        "user": {
            "id": record["id"],
            "email": payload.email,
            "access_token": session.session.access_token,
            "expires_at": jwt_expires_at,
            "role": role
        }
    }


##############################################################################
# Logout
##############################################################################

@router.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "success", "message": "Logged out"}

