import os
import bcrypt
from typing import Optional, List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_SUPA_URL = os.getenv("SUPABASE_URL")
_SUPA_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(_SUPA_URL, _SUPA_KEY)

##############################################################################
# Supabase helper functions
##############################################################################

def create_supabase_user(email: str, password: str) -> str:
    """
    Create a user in Supabase Auth and return its UUID.
    """
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    return res.user.id


def verify_password(plain: str, hashed: bytes) -> bool:
    """
    Compare plain text password with hashed version.
    """
    return bcrypt.checkpw(plain.encode(), hashed)


def hash_pw(plain: str) -> bytes:
    """
    Hash a plain text password.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())


def get_user_record(email: str) -> Optional[Dict]:
    """
    Return user record with fields: id, email, password_hash, role, permissions.
    """
    resp = supabase.table("users_app").select("*").eq("email", email).single().execute()
    return resp.data if resp.data else None


def insert_user_record(
    uid: str,
    email: str,
    hashed_pw: bytes,
    role: str = "client",
    permissions: Optional[List[str]] = None
) -> None:
    """
    Insert a user into 'users_app' table.
    """
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
    uid: str,
    fb_page_id: Optional[str] = None,
    fb_page_token: Optional[str] = None,
    ig_account_id: Optional[str] = None,
    tiktok_user_id: Optional[str] = None,
    tiktok_access_token: Optional[str] = None,
    tiktok_refresh_token: Optional[str] = None
) -> None:
    """
    Upsert social media credentials into the 'social_accounts' table.
    """
    supabase.table("social_accounts").upsert({
        "user_id": uid,
        "fb_page_id": fb_page_id,
        "fb_page_token": fb_page_token,
        "ig_account_id": ig_account_id,
        "tiktok_user_id": tiktok_user_id,
        "tiktok_access_token": tiktok_access_token,
        "tiktok_refresh_token": tiktok_refresh_token
    }).execute()


def get_social_by_uid(uid: str) -> Optional[Dict]:
    """
    Get all social account data for a given user_id.
    """
    res = supabase.table("social_accounts").select("*").eq("user_id", uid).single().execute()
    return res.data if res.data else None
