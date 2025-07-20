from fastapi import APIRouter, Request, HTTPException
from app.supabase_client import supabase

router = APIRouter()

@router.get("/api/social-accounts")
async def get_social_accounts(request: Request):
    print("Session:", request.session)
    user = request.session.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = user["id"]
        response = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
        print("Supabase response:", response)
        return {"accounts": response.data}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
