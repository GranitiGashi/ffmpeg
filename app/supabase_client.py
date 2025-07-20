import os
import bcrypt
from typing import Optional, List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_SUPA_URL = os.getenv("SUPABASE_URL")
_SUPA_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client(token: Optional[str] = None) -> Client:
    """Initialize Supabase client with optional auth token."""
    client = create_client(_SUPA_URL, _SUPA_KEY)
    if token:
        client.auth.set_auth(token)
    return client

supabase: Client = get_supabase_client()

##############################################################################
# Supabase helper functions
##############################################################################

def create_supabase_user(email: str, password: str) -> str:
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    return res.user.id

def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed)

def hash_pw(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())

def get_user_record(email: str) -> Optional[Dict]:
    resp = supabase.table("users_app").select("*").eq("email", email).single().execute()
    return resp.data if resp.data else None

def insert_user_record(
    uid: str,
    email: str,
    hashed_pw: bytes,
    role: str = "client",
    permissions: Optional[List[str]] = None
) -> None:
    if permissions is None:
        permissions = []
    supabase.table("users_app").insert({
        "id": uid,
        "email": email,
        "password_hash": hashed_pw.decode(),
        "role": role,
        "permissions": permissions
    }).execute()

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
        "metadata": metadata
    }).execute()

def get_social_by_uid(user_id: str) -> Optional[Dict]:
    res = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None