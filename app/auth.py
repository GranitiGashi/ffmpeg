from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.supabase_client import (
    supabase, create_supabase_user, hash_pw, get_user_record, insert_user_record, verify_password
)

router = APIRouter()


##############################################################################
# Sign-up (admin only) – optional
##############################################################################
class SignUpPayload(BaseModel):
    email: str
    password: str

@router.post("/api/signup")
async def signup(payload: SignUpPayload):
    try:
        uid = create_supabase_user(payload.email, payload.password)
        insert_user_record(uid, payload.email, hash_pw(payload.password))
        return {"status": "success", "message": "Account created"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

##############################################################################
# Login
##############################################################################
class LoginPayload(BaseModel):
    email: str
    password: str

@router.post("/api/login")
async def login(payload: LoginPayload, request: Request):
    record = get_user_record(payload.email)
    if not record or not verify_password(payload.password, record["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session = supabase.auth.sign_in_with_password({
        "email": payload.email,
        "password": payload.password
    })

    jwt_expires_at = session.session.expires_at

    # Optional: Store in session, or return JWT for frontend to store in localStorage
    request.session["user"] = {
        "id": record["id"],
        "email": payload.email,
        "jwt": session.session.access_token,
        "expires_at": jwt_expires_at
    }

    return {
        "status": "success",
        "user": {
            "id": record["id"],
            "email": payload.email,
            "access_token": session.session.access_token,
            "expires_at": jwt_expires_at
        }
    }


##############################################################################
# Logout
##############################################################################
@router.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "success", "message": "Logged out"}
