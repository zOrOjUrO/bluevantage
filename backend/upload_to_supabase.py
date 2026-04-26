import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(url, key)

# Load the generated fishing zones GeoJSON
# Assuming this is run from the backend directory
zones_file = Path('data/fishing_zones.json')

if not zones_file.exists():
    print(f"Error: {zones_file} not found. Run generate_zones.py first.")
    exit(1)

with open(zones_file, 'r') as f:
    geojson = json.load(f)

print(f"Uploading {len(geojson['features'])} zones to Supabase...")

# Prepare records for insertion
records = []
for feature in geojson['features']:
    props = feature['properties']
    # Mapping to Supabase schema (hexid, zonescore, port, zone_type)
    records.append({
        'hexid': props['h3_index'],
        'zonescore': props['probability'],
        'port': props['port'],
        'zone_type': props['zone_type']
    })

# Batch insert into 'zones' table in chunks
CHUNK_SIZE = 100
for i in range(0, len(records), CHUNK_SIZE):
    chunk = records[i:i + CHUNK_SIZE]
    try:
        # Use upsert to update existing hex IDs or insert new ones
        supabase.table('zones').upsert(chunk).execute()
        print(f"Uploaded chunk {i//CHUNK_SIZE + 1}/{(len(records)-1)//CHUNK_SIZE + 1}")
    except Exception as e:
        print(f"Error uploading chunk: {e}")

print("Upload complete!")
