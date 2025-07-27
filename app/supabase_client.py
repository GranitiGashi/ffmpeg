# supabase_client.py
import os
import bcrypt
from typing import Optional, List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv
import re
import requests
from datetime import datetime

load_dotenv()

_SUPA_URL = os.getenv("SUPABASE_URL")
_SUPA_KEY = os.getenv("SUPABASE_KEY")
_SUPA_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

def get_supabase_client(token: Optional[str] = None) -> Client:
    client = create_client(_SUPA_URL, _SUPA_SERVICE_ROLE)
    if token:
        client.auth.set_auth(token)
    return client

supabase: Client = get_supabase_client()

# Input sanitization
def sanitize_input(value: str) -> str:
    if not isinstance(value, str):
        return ""
    # Remove potentially dangerous characters
    return re.sub(r'[<>;]', '', value.strip())

def create_supabase_user(email: str, password: str, role: str = "client") -> str:
    # Validate email format
    email = sanitize_input(email)
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError("Invalid email format")
    
    # Validate password strength
    if len(password) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must be at least 8 characters and contain a special character")
    
    try:
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"role": role}
        })
        return res.user.id
    except Exception as e:
        raise ValueError(f"Failed to create user: {str(e)}")

def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed)

def hash_pw(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt())

def get_user_record(email: str) -> Optional[Dict]:
    email = sanitize_input(email)
    resp = supabase.table("users_app").select("*").eq("email", email).execute()
    data = resp.data
    return data[0] if data else None

def insert_user_record(
    uid: str,
    email: str,
    hashed_pw: bytes,
    full_name: str,
    company_name: str,
    role: str = "client",
    permissions: Optional[Dict] = None
) -> None:
    if permissions is None:
        permissions = {}

    # Sanitize inputs
    email = sanitize_input(email)
    full_name = sanitize_input(full_name)
    company_name = sanitize_input(company_name)
    role = sanitize_input(role)

    # Validate role
    if role not in ["client", "admin"]:
        raise ValueError("Invalid role specified")

    try:
        supabase.table("users_app").insert({
            "id": uid,
            "email": email,
            "password_hash": hashed_pw.decode('utf-8'),
            "full_name": full_name,
            "company_name": company_name,
            "role": role,
            "permissions": permissions,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        raise ValueError(f"Failed to insert user record: {str(e)}")

def upsert_social_record(
    user_id: str,
    provider: str,
    account_id: str,
    username: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    metadata: Optional[Dict] = None,
    token: Optional[str] = None
) -> None:
    if metadata is None:
        metadata = {}
    client = get_supabase_client(token)
    client.table("social_accounts").upsert({
        "user_id": user_id,
        "provider": provider,
        "account_id": account_id,
        "username": username,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "metadata": metadata,
        "created_at": None,
        "updated_at": None
    }).execute()

def get_social_accounts(user_id):
    response = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
    if response.error:
        raise Exception(response.error.message)
    return response.data

def test_connection():
    resp = supabase.table("users_app").select("*").limit(1).execute()
    print(f"Test query result: {resp.data}")
