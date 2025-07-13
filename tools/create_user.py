import sys, getpass, os, dotenv, uuid, bcrypt
# from app.supabase_client import (
#     create_supabase_user, insert_user_record, hash_pw
# )

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.supabase_client import (
    create_supabase_user,
    insert_user_record,
    hash_pw
)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/create_user.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    pwd = getpass.getpass("Password: ")
    uid = create_supabase_user(email, pwd)
    insert_user_record(uid, email, hash_pw(pwd))
    print("✅ user created:", uid)
