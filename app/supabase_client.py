import os, bcrypt, uuid
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

_SUPA_URL  = "https://flrutigkqwbtpeobchkd.supabase.co"
_SUPA_KEY  = "YOUR_SUPABASE_SERVICE_ROLE_KEY"  # replace with env or secret manager

supabase: Client = create_client(_SUPA_URL, _SUPA_KEY)

##############################################################################
# Supabase helper functions
##############################################################################

def create_supabase_user(email: str, password: str) -> str:
    """Create a user in Supabase Auth and return its UUID."""
    res = supabase.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    )
    return res.user.id

def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed)

def hash_pw(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())

def get_user_record(email: str):
    """Return dict with keys: id, email, password_hash, role, permissions."""
    resp = supabase.table("users_app").select("*").eq("email", email).single().execute()
    return resp.data if resp.data else None

def insert_user_record(uid: str, email: str, hashed_pw: bytes, role: str = "client", permissions: list[str] = []):
    supabase.table("users_app").insert({
        "id": uid,             # same as auth.users UUID
        "email": email,
        "password_hash": hashed_pw.decode(),
        "role": role,
        "permissions": permissions
    }).execute()

def upsert_social_record(
    uid: str,
    fb_page_id: str = None,
    fb_page_token: str = None,
    ig_account_id: str = None,
    tiktok_user_id: str = None,
    tiktok_access_token: str = None,
    tiktok_refresh_token: str = None
):
    """Upsert FB/IG/TikTok data in one social_accounts row."""
    supabase.table("social_accounts").upsert({
        "user_id": uid,
        "fb_page_id": fb_page_id,
        "fb_page_token": fb_page_token,
        "ig_account_id": ig_account_id,
        "tiktok_user_id": tiktok_user_id,
        "tiktok_access_token": tiktok_access_token,
        "tiktok_refresh_token": tiktok_refresh_token
    }).execute()

def get_social_by_uid(uid: str):
    """Returns all social account fields for a given user_id."""
    res = (supabase.table("social_accounts")
                  .select("*")
                  .eq("user_id", uid)
                  .single()
                  .execute())
    return res.data
