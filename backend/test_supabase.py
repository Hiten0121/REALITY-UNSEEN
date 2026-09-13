from app.db import get_supabase

print("Creating Supabase client...")

supabase = get_supabase()

print("Testing Supabase API key...")

try:
    response = (
        supabase
        .table("stories")
        .select("id")
        .limit(1)
        .execute()
    )

    print("===================================")
    print("SUPABASE API KEY WORKS")
    print("===================================")
    print(response.data)

except Exception as e:
    print("===================================")
    print("SUPABASE API KEY FAILED")
    print(type(e).__name__)
    print(str(e))
    print("===================================")