from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import List, Optional, Dict, Any
import os
from urllib.parse import quote
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

app = FastAPI(title="BlueVantage API", version="1.0.0")

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

# Pydantic models for zones data
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
    client: httpx.AsyncClient, headers: Dict[str, str], hex_id: str
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch zone by trying both possible id columns (hex_id, hexid)."""
    encoded_hex_id = hex_id.replace('"', '\\"')
    for id_col in ["hex_id", "hexid"]:
        url = f"{SUPABASE_URL}/rest/v1/zones?{id_col}=eq.{encoded_hex_id}"
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            zone_data = response.json()
            if zone_data:
                return zone_data[0], id_col
        elif response.status_code in [401, 403]:
            raise HTTPException(status_code=response.status_code, detail=f"Supabase auth error: {response.text}")
        elif response.status_code == 400 and "42703" in response.text:
            continue
        else:
            logger.error(f"Unexpected Supabase response while fetching zone: {response.status_code} - {response.text}")
    return None, None

@app.get("/")
async def root():
    return {"status": "BlueVantage API v1.0", "docs": "/docs"}

@app.get("/api/zones", response_model=Dict[str, Any])
async def get_all_zones(
    species: Optional[str] = Query(None, description="Filter by species name"),
    port: Optional[str] = Query(None, description="Filter by port name (e.g., Urk)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sortby: Optional[str] = Query(None, description="Sort field (zonescore, windkmh, waveheightm, distancekm)")
):
    """
    Fetch all fishing zones from Supabase with optional filtering and pagination.
    
    Parameters:
    - species: Filter by target species (optional)
    - limit: Maximum number of zones to return (1-1000, default: 100)
    - offset: Pagination offset (default: 0)
    - sortby: Sort results by field (zonescore, windkmh, waveheightm, distancekm)
    
    Returns zones data including coordinates, yields, conditions, and slot availability.
    """
    if not SUPABASE_KEY:
        logger.error("SUPABASE_KEY not configured")
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API credentials")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            # Build query parameters
            query_params = f"limit={limit}&offset={offset}"
            
            sort_map = {
                "zonescore": ["zone_score", "zonescore"],
                "windkmh": ["wind_kmh", "windkmh"],
                "waveheightm": ["wave_height_m", "waveheightm"],
                "distancekm": ["distance_km", "distancekm"],
            }
            if sortby and sortby in sort_map:
                # Prefer snake_case (current DB schema), fallback handled by Supabase if present.
                query_params += f"&order={sort_map[sortby][0]}.desc"

            if port:
                port_response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/ports?name=eq.{quote(port, safe='')}&select=id",
                    headers=headers,
                )
                if port_response.status_code == 200:
                    port_rows = port_response.json()
                    if not port_rows:
                        return {
                            "success": True,
                            "zones": [],
                            "count": 0,
                            "limit": limit,
                            "offset": offset,
                            "total_returned": 0,
                            "port": port,
                        }
                    port_id = port_rows[0]["id"]
                    query_params += f"&port_id=eq.{port_id}"
            
            url = f"{SUPABASE_URL}/rest/v1/zones?{query_params}"
            
            logger.info(f"Fetching zones from Supabase: {url[:80]}...")
            response = await client.get(url, headers=headers)
            
            if response.status_code == 401:
                logger.error("Unauthorized access to Supabase")
                raise HTTPException(status_code=401, detail="Authentication failed with Supabase")
            elif response.status_code == 403:
                logger.error("Forbidden access to Supabase zones table")
                raise HTTPException(status_code=403, detail="Access denied to zones table")
            elif response.status_code != 200:
                logger.error(f"Supabase error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Supabase error: {response.text}")
            
            raw_zones = response.json()
            
            if not isinstance(raw_zones, list):
                logger.error(f"Unexpected response format from Supabase: {type(raw_zones)}")
                raise HTTPException(status_code=500, detail="Invalid response format from database")

            zones = [normalize_zone(zone) for zone in raw_zones]
            
            # Filter by species if requested
            if species:
                filtered_zones = []
                for zone in zones:
                    if "species" in zone and isinstance(zone["species"], list):
                        for sp in zone["species"]:
                            if isinstance(sp, dict) and sp.get("name", "").lower() == species.lower():
                                filtered_zones.append(zone)
                                break
                zones = filtered_zones
                logger.info(f"Filtered to {len(zones)} zones for species: {species}")
            
            return {
                "success": True,
                "zones": zones,
                "count": len(zones),
                "limit": limit,
                "offset": offset,
                "total_returned": len(zones),
                "port": port,
            }
    except httpx.TimeoutException:
        logger.error("Request to Supabase timed out")
        raise HTTPException(status_code=504, detail="Request timeout: Database took too long to respond")
    except httpx.ConnectError:
        logger.error("Failed to connect to Supabase")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Unexpected error fetching zones: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

@app.get("/api/zones/{hex_id}", response_model=Dict[str, Any])
async def get_zone_detail(hex_id: str):
    """
    Get detailed information for a specific fishing zone by hexid.
    
    Parameters:
    - hex_id: The hexagonal zone identifier
    
    Returns full zone details including coordinates, environmental conditions,
    species availability, yield estimates, and slot information.
    """
    if not SUPABASE_KEY:
        logger.error("SUPABASE_KEY not configured")
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API credentials")
    
    if not hex_id or not hex_id.strip():
        raise HTTPException(status_code=400, detail="Invalid hex_id: Must be a non-empty string")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            write_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
            headers = {
                "apikey": write_key,
                "Authorization": f"Bearer {write_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Fetching zone details for hexid: {hex_id}")
            zone, _ = await fetch_zone_by_hex(client, headers, hex_id)
            if not zone:
                logger.warning(f"Zone not found: {hex_id}")
                raise HTTPException(status_code=404, detail=f"Zone with hexid '{hex_id}' not found")
            logger.info(f"Successfully retrieved zone: {hex_id}")
            
            return {
                "success": True,
                "zone": normalize_zone(zone)
            }
    except httpx.TimeoutException:
        logger.error("Request to Supabase timed out")
        raise HTTPException(status_code=504, detail="Request timeout: Database took too long to respond")
    except httpx.ConnectError:
        logger.error("Failed to connect to Supabase")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching zone {hex_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

@app.post("/api/zones/{hex_id}/reserve", response_model=Dict[str, Any])
async def reserve_zone_slot(hex_id: str, request: ReservationRequest):
    """
    Reserve a fishing slot in a zone and increment slots_filled.
    
    Parameters:
    - hex_id: The hexagonal zone identifier
    - fisher_id: Unique identifier for the fisher
    - time_window: Booking window ("morning", "full_day", "overnight")
    
    Returns confirmation with reservation details.
    """
    if not SUPABASE_KEY:
        logger.error("SUPABASE_KEY not configured")
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API credentials")
    
    if not request.fisher_id or not request.fisher_id.strip():
        raise HTTPException(status_code=400, detail="Invalid fisher_id: Must be a non-empty string")
    
    if request.time_window not in ["morning", "full_day", "overnight"]:
        raise HTTPException(status_code=400, detail="Invalid time_window: Must be one of 'morning', 'full_day', 'overnight'")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            # First, get current slot count
            zone, id_col = await fetch_zone_by_hex(client, headers, hex_id)
            if not zone or not id_col:
                raise HTTPException(status_code=404, detail=f"Zone {hex_id} not found")

            slots_filled_col = "slots_filled" if "slots_filled" in zone else "slotsfilled"
            slots_total_col = "slots_total" if "slots_total" in zone else "slotstotal"
            slots_filled = zone.get(slots_filled_col, 0) or 0
            slots_total = zone.get(slots_total_col, 0) or 0
            
            # Check if slots available
            if slots_filled >= slots_total:
                logger.warning(f"No slots available for zone {hex_id}")
                raise HTTPException(status_code=409, detail=f"No slots available in zone {hex_id}")
            
            # Increment slots_filled
            new_slots_filled = slots_filled + 1
            update_url = f"{SUPABASE_URL}/rest/v1/zones?{id_col}=eq.{hex_id}"
            update_response = await client.patch(
                update_url,
                headers=headers,
                json={slots_filled_col: new_slots_filled}
            )
            
            if update_response.status_code not in [200, 204]:
                logger.error(f"Failed to update zone slots: {update_response.text}")
                raise HTTPException(status_code=500, detail="Failed to update zone reservation")
            
            logger.info(f"Successfully reserved slot in zone {hex_id} for fisher {request.fisher_id}")
            
            return {
                "success": True,
                "status": "reserved",
                "zone": hex_id,
                "fisher": request.fisher_id,
                "window": request.time_window,
                "confirmation": f"RES-{hex_id}-{int(__import__('time').time())}",
                "slots_filled": new_slots_filled,
                "slots_total": slots_total
            }
    except httpx.TimeoutException:
        logger.error("Request to Supabase timed out")
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.ConnectError:
        logger.error("Failed to connect to Supabase")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error reserving slot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

@app.post("/api/logbook", response_model=Dict[str, Any])
async def create_logbook_entry(entry: LogbookEntry):
    """
    Create a new logbook entry (fishing catch record).
    
    Parameters:
    - fisher_id: Unique identifier for the fisher
    - zone_id: Hexagonal zone identifier where fishing occurred
    - timestamp: ISO 8601 timestamp (optional, defaults to now)
    - species_caught: Array of species with counts/weights
    - total_kg: Total catch weight in kilograms
    - notes: Additional notes about the catch
    
    Returns the created logbook entry with ID.
    """
    if not SUPABASE_KEY:
        logger.error("SUPABASE_KEY not configured")
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API credentials")
    
    if not entry.fisher_id or not entry.fisher_id.strip():
        raise HTTPException(status_code=400, detail="Invalid fisher_id: Must be a non-empty string")
    
    if not entry.zone_id or not entry.zone_id.strip():
        raise HTTPException(status_code=400, detail="Invalid zone_id: Must be a non-empty string")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            # Match current Supabase logbook_entries schema (fisher_id, hex_id, species_caught, weight_kg).
            payload = {
                "fisher_id": entry.fisher_id,
                "hex_id": entry.zone_id,
            }
            if entry.species_caught is not None:
                payload["species_caught"] = entry.species_caught
            if entry.total_kg is not None:
                payload["weight_kg"] = entry.total_kg

            url = f"{SUPABASE_URL}/rest/v1/logbook_entries"
            result = None
            last_error_text = None
            auth_or_policy_error = None
            schema_error = None
            response = await client.post(
                url,
                headers={**headers, "Prefer": "return=representation"},
                json=payload
            )
            if response.status_code in [200, 201]:
                data = response.json()
                result = data[0] if isinstance(data, list) and data else data
            else:
                last_error_text = response.text
                if response.status_code in [401, 403] or "row-level security policy" in response.text.lower():
                    auth_or_policy_error = response.text
                elif response.status_code in [400, 422] and ("42703" in response.text or "PGRST204" in response.text):
                    schema_error = response.text
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="logbook_entries table not found")
            if result is None:
                if auth_or_policy_error:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Logbook insert blocked by Supabase policy: {auth_or_policy_error}",
                    )
                if schema_error:
                    raise HTTPException(
                        status_code=400,
                        detail=f"logbook_entries schema mismatch for provided payload: {schema_error}",
                    )
                logger.error(f"Failed to create logbook entry: {last_error_text}")
                raise HTTPException(status_code=500, detail=f"Failed to create logbook entry: {last_error_text}")

            logger.info(f"Created logbook entry for fisher {entry.fisher_id} in zone {entry.zone_id}")
            
            return {
                "success": True,
                "message": "Logbook entry created successfully",
                "entry": result if isinstance(result, dict) else {"fisher_id": entry.fisher_id, "zone_id": entry.zone_id}
            }
    except httpx.TimeoutException:
        logger.error("Request to Supabase timed out")
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.ConnectError:
        logger.error("Failed to connect to Supabase")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating logbook entry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

@app.get("/api/ports", response_model=Dict[str, Any])
async def get_ports():
    """
    Fetch all fishing ports.
    
    Returns list of ports with names and coordinates.
    """
    if not SUPABASE_KEY:
        logger.error("SUPABASE_KEY not configured")
        raise HTTPException(status_code=500, detail="Server configuration error: Missing API credentials")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            url = f"{SUPABASE_URL}/rest/v1/ports?order=name.asc"
            logger.info(f"Fetching ports from Supabase...")
            response = await client.get(url, headers=headers)
            
            if response.status_code == 401:
                logger.error("Unauthorized access to Supabase")
                raise HTTPException(status_code=401, detail="Authentication failed with Supabase")
            elif response.status_code == 403:
                logger.error("Forbidden access to ports table")
                raise HTTPException(status_code=403, detail="Access denied to ports table")
            elif response.status_code != 200:
                logger.error(f"Supabase error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Supabase error: {response.text}")
            
            raw_ports = response.json()
            
            if not isinstance(raw_ports, list):
                logger.error(f"Unexpected response format from Supabase: {type(raw_ports)}")
                raise HTTPException(status_code=500, detail="Invalid response format from database")

            ports = [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "lat": p.get("lat"),
                    "lon": p.get("lon") if p.get("lon") is not None else p.get("lng"),
                    "country": p.get("country"),
                    "active": p.get("active"),
                }
                for p in raw_ports
            ]
            
            logger.info(f"Successfully retrieved {len(ports)} ports")
            
            return {
                "success": True,
                "ports": ports,
                "count": len(ports)
            }
    except httpx.TimeoutException:
        logger.error("Request to Supabase timed out")
        raise HTTPException(status_code=504, detail="Request timeout: Database took too long to respond")
    except httpx.ConnectError:
        logger.error("Failed to connect to Supabase")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching ports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
