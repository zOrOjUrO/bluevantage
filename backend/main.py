from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import List, Optional, Dict, Any
import os
from urllib.parse import quote
from dotenv import load_dotenv
import logging
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(override=True)

app = FastAPI(title="BlueVantage API", version="1.0.0")

# Load ML model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "models", "xgboost_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
    logger.info(f"Successfully loaded model from {MODEL_PATH}")
except Exception as e:
    model = None
    logger.error(f"Failed to load model: {e}")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.vercel.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tnapfawdehztxsqmoeyy.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate required environment variables
if not SUPABASE_KEY:
    logger.warning("SUPABASE_KEY not set in environment variables")

# Pydantic models
class SpeciesData(BaseModel):
    name: str
    abundance: Optional[str] = None

class ZoneData(BaseModel):
    hexid: str
    lat: float
    lon: float
    zonescore: Optional[float] = None
    species: List[Dict[str, Any]]
    yieldlowkg: Optional[float] = None
    yieldhighkg: Optional[float] = None
    slotstotal: Optional[int] = None
    slotsfilled: Optional[int] = None
    waveheightm: Optional[float] = None
    windkmh: Optional[float] = None
    ismpa: Optional[bool] = None
    distancekm: Optional[float] = None

class ReservationRequest(BaseModel):
    fisher_id: str
    time_window: str

class LogbookEntry(BaseModel):
    fisher_id: str
    zone_id: str
    timestamp: Optional[str] = None
    species_caught: Optional[List[Dict[str, Any]]] = None
    total_kg: Optional[float] = None
    notes: Optional[str] = None

class Port(BaseModel):
    id: Optional[int] = None
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None

def normalize_zone(zone: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize DB column naming variants to API contract names."""
    return {
        "hexid": zone.get("hexid") or zone.get("hex_id"),
        "lat": zone.get("lat"),
        "lon": zone.get("lon") if zone.get("lon") is not None else zone.get("lng"),
        "zonescore": zone.get("zonescore") if zone.get("zonescore") is not None else zone.get("zone_score"),
        "species": zone.get("species") or [],
        "yieldlowkg": zone.get("yieldlowkg") if zone.get("yieldlowkg") is not None else zone.get("yield_low_kg"),
        "yieldhighkg": zone.get("yieldhighkg") if zone.get("yieldhighkg") is not None else zone.get("yield_high_kg"),
        "slotstotal": zone.get("slotstotal") if zone.get("slotstotal") is not None else zone.get("slots_total"),
        "slotsfilled": zone.get("slotsfilled") if zone.get("slotsfilled") is not None else zone.get("slots_filled"),
        "waveheightm": zone.get("waveheightm") if zone.get("waveheightm") is not None else zone.get("wave_height_m"),
        "windkmh": zone.get("windkmh") if zone.get("windkmh") is not None else zone.get("wind_kmh"),
        "ismpa": zone.get("ismpa") if zone.get("ismpa") is not None else zone.get("is_mpa"),
        "distancekm": zone.get("distancekm") if zone.get("distancekm") is not None else zone.get("distance_km"),
        "port_id": zone.get("port_id"),
    }

async def fetch_zone_by_hex(
    client: httpx.AsyncClient, 
    headers: Dict[str, str], 
    hex_id: str
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch zone by trying both possible id columns (hex_id, hexid)."""
    encoded_hex_id = hex_id.replace('"', '\\\\"')
    for id_col in ["hex_id", "hexid"]:
        url = f"{SUPABASE_URL}/rest/v1/zones?{id_col}=eq.{encoded_hex_id}"
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            zone_data = response.json()
            if zone_data:
                return zone_data[0], id_col
    return None, None

@app.get("/")
async def root():
    return {"status": "BlueVantage API v1.0", "docs": "/docs", "model_loaded": model is not None}

@app.get("/api/zones")
async def get_all_zones(
    species: Optional[str] = Query(None),
    port: Optional[str] = Query(None),
    limit: int = 100,
    offset: int = 0,
    sortby: Optional[str] = None
):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            query_params = f"limit={limit}&offset={offset}"
            
            if port:
                port_res = await client.get(f"{SUPABASE_URL}/rest/v1/ports?name=eq.{quote(port)}&select=id", headers=headers)
                if port_res.status_code == 200 and port_res.json():
                    query_params += f"&port_id=eq.{port_res.json()[0]['id']}"
            
            url = f"{SUPABASE_URL}/rest/v1/zones?{query_params}"
            response = await client.get(url, headers=headers)
            raw_zones = response.json()
            zones = [normalize_zone(z) for z in raw_zones]
            
            if species:
                zones = [z for z in zones if any(s.get('name', '').lower() == species.lower() for s in z.get('species', []))]
            
            return {"success": True, "zones": zones, "count": len(zones)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predict/{hex_id}")
async def predict_zone(hex_id: str):
    """Run live prediction for a zone using the trained XGBoost model."""
    if not model:
        raise HTTPException(status_code=503, detail="Prediction model not loaded")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            zone, _ = await fetch_zone_by_hex(client, headers, hex_id)
            if not zone:
                raise HTTPException(status_code=404, detail="Zone not found")
            
            # Prepare features (matching the notebook pipeline)
            # features = [sst, chl, depth, week, ...]
            # For simplicity, we assume features are stored in the zone record
            features = [
                zone.get("sst_value", 12.0),
                zone.get("chl_value", 1.0),
                zone.get("depth", 20.0),
                zone.get("season_week", 15)
            ]
            
            prediction = model.predict([features])[0]
            species_list = ["plaice", "sole", "cod", "herring", "mackerel"]
            scores = {species_list[i]: float(prediction[i]) for i in range(len(species_list))}
            
            return {
                "success": True,
                "hexid": hex_id,
                "predictions": scores,
                "top_species": max(scores, key=scores.get)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/api/zones/{hex_id}/reserve")
async def reserve_zone_slot(hex_id: str, request: ReservationRequest):
    async with httpx.AsyncClient() as client:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        zone, id_col = await fetch_zone_by_hex(client, headers, hex_id)
        if not zone: raise HTTPException(status_code=404, detail="Zone not found")
        
        filled = (zone.get("slots_filled") or 0) + 1
        update_url = f"{SUPABASE_URL}/rest/v1/zones?{id_col}=eq.{hex_id}"
        await client.patch(update_url, headers=headers, json={"slots_filled": filled})
        return {"success": True, "hexid": hex_id, "slots_filled": filled}

@app.post("/api/logbook")
async def create_logbook_entry(entry: LogbookEntry):
    async with httpx.AsyncClient() as client:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        payload = {"fisher_id": entry.fisher_id, "hex_id": entry.zone_id, "weight_kg": entry.total_kg}
        await client.post(f"{SUPABASE_URL}/rest/v1/logbook_entries", headers=headers, json=payload)
        return {"success": True}

@app.get("/api/ports")
async def get_ports():
    async with httpx.AsyncClient() as client:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = await client.get(f"{SUPABASE_URL}/rest/v1/ports?order=name.asc", headers=headers)
        return {"success": True, "ports": response.json()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
