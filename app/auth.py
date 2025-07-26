# app/auth.py
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field
from app.supabase_client import (
    supabase, create_supabase_user, hash_pw,
    get_user_record, insert_user_record, verify_password
)
from jose import jwt, jwk
from jose.utils import base64url_decode
import os
import requests
from typing import Dict
from functools import lru_cache
from datetime import datetime
import logging

router = APIRouter()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Env vars
SUPABASE_URL = os.getenv("SUPABASE_URL")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

###############################################################################
# Models
###############################################################################

class SignUpPayload(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str
    company_name: str
    role: str = Field(default="client")
    permissions: Dict = Field(default_factory=dict)

class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

###############################################################################
# JWT Verifier
###############################################################################

@lru_cache()
def fetch_jwks():
    res = requests.get(JWKS_URL)
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Unable to fetch JWKS")
    return res.json()["keys"]

def verify_admin_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Invalid token header")

    key = next((k for k in fetch_jwks() if k["kid"] == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid signing key")

    public_key = jwk.construct(key)
    message, encoded_sig = token.rsplit(".", 1)
    decoded_sig = base64url_decode(encoded_sig.encode())

    if not public_key.verify(message.encode(), decoded_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_aud": False})

    if payload.get("role") != "authenticated" or payload.get("user_metadata", {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return payload

###############################################################################
# Routes
###############################################################################

@router.post("/api/signup")
async def signup(payload: SignUpPayload, user_info: Dict = Depends(verify_admin_token)):
    existing_user = get_user_record(payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    uid = create_supabase_user(payload.email, payload.password, payload.role)
    hashed_password = hash_pw(payload.password)

    insert_user_record(
        uid=uid,
        email=payload.email,
        hashed_pw=hashed_password,
        full_name=payload.full_name,
        company_name=payload.company_name,
        role=payload.role,
        permissions=payload.permissions
    )

    return {"status": "success", "user_id": uid}

@router.post("/api/login")
async def login(payload: LoginPayload, request: Request):
    record = get_user_record(payload.email)
    if not record or not verify_password(payload.password, record["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session = supabase.auth.sign_in_with_password({
        "email": payload.email,
        "password": payload.password
    })

    if not session.session:
        raise HTTPException(status_code=401, detail="Login failed")

    request.session["user"] = {
        "id": record["id"],
        "email": record["email"],
        "jwt": session.session.access_token,
        "expires_at": session.session.expires_at,
        "role": record.get("role", "client")
    }

    return {"status": "success", "access_token": session.session.access_token}

@router.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "success", "message": "Logged out"}