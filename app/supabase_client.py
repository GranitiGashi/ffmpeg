import os, bcrypt, uuid
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

# _SUPA_URL  = os.getenv("SUPABASE_URL")
# _SUPA_KEY  = os.getenv("SUPABASE_KEY")

_SUPA_URL  = "https://flrutigkqwbtpeobchkd.supabase.co"
_SUPA_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZscnV0aWdrcXdidHBlb2JjaGtkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjQxMzM4NCwiZXhwIjoyMDY3OTg5Mzg0fQ.UsDC34CSOIGvZqFRsqqoCLAFljjdWyvPMYe5EXE_owQ"

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
    """Return dict with keys: id, email, password_hash."""
    resp = supabase.table("users_app").select("*").eq("email", email).single().execute()
    return resp.data if resp.data else None

def insert_user_record(uid: str, email: str, hashed_pw: bytes):
    supabase.table("users_app").insert({
        "id": uid,             # same as auth.users UUID
        "email": email,
        "password_hash": hashed_pw.decode(),
    }).execute()

def upsert_social_record(uid: str, page_id: str, page_tok: str, ig_id: str | None):
    supabase.table("social_accounts").upsert({
        "user_id": uid,
        "fb_page_id": page_id,
        "fb_page_token": page_tok,
        "ig_account_id": ig_id,
    }).execute()

def get_social_by_uid(uid: str):
    res = (supabase.table("social_accounts")
                  .select("fb_page_token, ig_account_id")
                  .eq("user_id", uid)
                  .single()
                  .execute())
    return res.data
