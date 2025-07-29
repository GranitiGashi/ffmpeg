# app/auth.py
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field
from app.supabase_client import (
    supabase, create_supabase_user, hash_pw,
    get_user_record, insert_user_record, verify_password
)
from jose import JWTError, jwt
import os
from typing import Dict
from datetime import datetime, timedelta
import logging

router = APIRouter()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SECRET_KEY = "aff51256575b1b07cc23ec80c8ddb362"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

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
# JWT Utilities
###############################################################################

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    return decode_token(token)

def verify_admin_token(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

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

    token = create_access_token({"sub": payload.email, "role": payload.role})
    return {"status": "success", "user_id": uid, "token": token}

@router.post("/api/login")
async def login(payload: LoginPayload):
    record = get_user_record(payload.email)
    if not record or not verify_password(payload.password, record["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": payload.email, "role": record.get("role", "client")})
    return {
        "status": "success",
          "access_token": token,
          "email": payload.email,
          "role": record.get("role", "client")
          }

@router.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "success", "message": "Logged out"}
