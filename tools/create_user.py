import sys
import getpass
import os
import dotenv
import uuid
import bcrypt
import importlib.util
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Load environment variables
dotenv.load_dotenv()

# Ensure the app directory is in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

# Dynamically check and import supabase_client
supabase_client_path = os.path.join(project_root, "app", "supabase_client.py")
if not os.path.exists(supabase_client_path):
    print(f"Error: Could not find supabase_client.py at {supabase_client_path}")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("supabase_client", supabase_client_path)
supabase_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_client)

create_supabase_user = supabase_client.create_supabase_user
insert_user_record = supabase_client.insert_user_record
hash_pw = supabase_client.hash_pw

# Initialize Supabase client with service role key for admin operations and custom timeout
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_SERVICE_ROLE_KEY not found in .env file")
    sys.exit(1)

# Configure client with increased timeout
options = ClientOptions()  # 30 seconds timeout
admin_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, options=options)

# Test connection
try:
    response = admin_supabase.table("users_app").select("*").limit(1).execute()
    print(f"Connection test successful: {response.data}")
except Exception as e:
    print(f"Connection test failed: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/create_user.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    pwd = getpass.getpass("Password: ")
    
    # Prompt for optional fields
    full_name = input("Full Name (optional, press Enter to skip): ").strip() or None
    company_name = input("Company Name (optional, press Enter to skip): ").strip() or None
    role = input("Role (default 'client', press Enter for default): ").strip() or "client"
    permissions = input("Permissions (JSON array, e.g., [], press Enter for []): ").strip() or "[]"

    try:
        # Create Supabase auth user using admin client
        uid = admin_supabase.auth.admin.create_user({
            "email": email,
            "password": pwd,
            "email_confirm": True
        }).user.id
        
        # Hash the password
        hashed_pw = hash_pw(pwd)
        
        # Insert user record
        insert_user_record(
            uid=uid,
            email=email,
            hashed_pw=hashed_pw,
            role=role,
            permissions=eval(permissions) if permissions else []
        )
        
        print(f"✅ User created: {uid}")
        print(f"Details - Email: {email}, Role: {role}, Full Name: {full_name}, Company Name: {company_name}")
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        sys.exit(1)