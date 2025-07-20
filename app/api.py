from fastapi import APIRouter, Request, HTTPException
from app.supabase_client import supabase

router = APIRouter()

@router.get("/api/social-accounts")
async def get_social_accounts(request: Request):
    user = request.session.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = user["id"]
    response = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
    if response.error:  # Check if error exists in the response
        raise HTTPException(status_code=500, detail=f"Failed to fetch social accounts: {response.error.message}")
    
    accounts = response.data
    return {"accounts": accounts}