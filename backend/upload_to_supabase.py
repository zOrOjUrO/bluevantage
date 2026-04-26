import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Load your zones.json from Jupyter notebook output
with open('../data/zones/zones.json', 'r') as f:
    zones = json.load(f)

# Batch insert
for zone in zones:
    try:
        data = supabase.table('zones').insert(zone).execute()
        print(f"✓ Uploaded {zone['hexid']}")
    except Exception as e:
        print(f"✗ Error: {e}")