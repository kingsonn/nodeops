"""
Test script to debug delete holding operation
"""
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {'*' * 20 if SUPABASE_KEY else 'NOT SET'}")

# Create client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n=== Testing Holdings Table ===")

# 1. List all holdings
print("\n1. Fetching all holdings...")
try:
    holdings = client.table("holdings").select("*").execute()
    print(f"✅ Found {len(holdings.data)} holdings:")
    for h in holdings.data:
        print(f"   - ID: {h['id']}, Portfolio: {h.get('portfolio_id')}, Symbol: {h.get('token_symbol')}, Amount: {h.get('amount')}")
except Exception as e:
    print(f"❌ Error fetching holdings: {e}")

# 2. Check holdings table schema
print("\n2. Checking holdings table columns...")
try:
    # Get first holding to see columns
    if holdings.data and len(holdings.data) > 0:
        first_holding = holdings.data[0]
        print(f"✅ Holdings table columns: {list(first_holding.keys())}")
    else:
        print("⚠️ No holdings found to check schema")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Test delete operation
print("\n3. Testing delete operation...")
if holdings.data and len(holdings.data) > 0:
    test_holding_id = holdings.data[0]['id']
    print(f"   Attempting to delete holding ID: {test_holding_id}")
    
    try:
        # Try to delete
        delete_response = client.table("holdings").delete().eq("id", test_holding_id).execute()
        print(f"✅ Delete response: {delete_response}")
        print(f"✅ Delete successful!")
        
        # Verify deletion
        verify = client.table("holdings").select("*").eq("id", test_holding_id).execute()
        if not verify.data or len(verify.data) == 0:
            print(f"✅ Verified: Holding {test_holding_id} was deleted")
        else:
            print(f"⚠️ Warning: Holding {test_holding_id} still exists")
            
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   Error details: {str(e)}")
else:
    print("⚠️ No holdings to test delete")

print("\n=== Test Complete ===")
