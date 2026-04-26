# BlueVantage API Documentation

## Overview
The BlueVantage API provides endpoints to fetch fishing zone data from Supabase, including environmental conditions, species availability, and slot information.

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require Supabase credentials set via environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anonymous/service role API key

## Zones Table Schema
The `zones` table contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `hexid` | STRING | Unique hexagonal zone identifier |
| `lat` | FLOAT | Latitude coordinate |
| `lon` | FLOAT | Longitude coordinate |
| `zonescore` | FLOAT | Zone quality/suitability score (0-100) |
| `species` | JSONB[] | Array of species objects with `name`, `abundance`, etc. |
| `yieldlowkg` | FLOAT | Low estimate yield in kilograms |
| `yieldhighkg` | FLOAT | High estimate yield in kilograms |
| `slotstotal` | INT | Total available fishing slots |
| `slotsfilled` | INT | Currently filled slots |
| `waveheightm` | FLOAT | Current wave height in meters |
| `windkmh` | FLOAT | Current wind speed in km/h |
| `ismpa` | BOOLEAN | Is this a Marine Protected Area? |
| `distancekm` | FLOAT | Distance from reference point in kilometers |

## API Endpoints

### 1. Get All Zones
Fetch all fishing zones with optional filtering and pagination.

**Endpoint:**
```
GET /api/zones
```

**Query Parameters:**
- `species` (optional): Filter by species name (e.g., "plaice", "sole", "cod")
- `limit` (optional, default: 100): Maximum number of results (1-1000)
- `offset` (optional, default: 0): Pagination offset
- `sortby` (optional): Sort field - one of: `zonescore`, `windkmh`, `waveheightm`, `distancekm`

**Example Requests:**
```bash
# Get all zones
curl "http://localhost:8000/api/zones"

# Get zones filtered by species
curl "http://localhost:8000/api/zones?species=plaice"

# Get zones sorted by zone score with pagination
curl "http://localhost:8000/api/zones?sortby=zonescore&limit=50&offset=0"

# Combined filters
curl "http://localhost:8000/api/zones?species=cod&sortby=windkmh&limit=25"
```

**Response (200 OK):**
```json
{
  "success": true,
  "zones": [
    {
      "hexid": "hex_001",
      "lat": 52.5200,
      "lon": 13.4050,
      "zonescore": 85.5,
      "species": [
        {
          "name": "plaice",
          "abundance": "high"
        }
      ],
      "yieldlowkg": 150.0,
      "yieldhighkg": 250.0,
      "slotstotal": 20,
      "slotsfilled": 15,
      "waveheightm": 1.2,
      "windkmh": 12.5,
      "ismpa": false,
      "distancekm": 45.3
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0,
  "total_returned": 1
}
```

**Error Responses:**
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Authentication failed with Supabase
- `403 Forbidden`: Access denied to zones table
- `500 Internal Server Error`: Server configuration error or unexpected error
- `503 Service Unavailable`: Database connection failed
- `504 Gateway Timeout`: Request timeout

---

### 2. Get Zone Details
Fetch detailed information for a specific fishing zone by hexid.

**Endpoint:**
```
GET /api/zones/{hex_id}
```

**Path Parameters:**
- `hex_id` (required): The hexagonal zone identifier (e.g., "hex_001")

**Example Requests:**
```bash
# Get details for a specific zone
curl "http://localhost:8000/api/zones/hex_001"
```

**Response (200 OK):**
```json
{
  "success": true,
  "zone": {
    "hexid": "hex_001",
    "lat": 52.5200,
    "lon": 13.4050,
    "zonescore": 85.5,
    "species": [
      {
        "name": "plaice",
        "abundance": "high"
      },
      {
        "name": "sole",
        "abundance": "medium"
      }
    ],
    "yieldlowkg": 150.0,
    "yieldhighkg": 250.0,
    "slotstotal": 20,
    "slotsfilled": 15,
    "waveheightm": 1.2,
    "windkmh": 12.5,
    "ismpa": false,
    "distancekm": 45.3
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid or empty hex_id
- `401 Unauthorized`: Authentication failed with Supabase
- `403 Forbidden`: Access denied to zones table
- `404 Not Found`: Zone with specified hexid not found
- `500 Internal Server Error`: Server configuration error or unexpected error
- `503 Service Unavailable`: Database connection failed
- `504 Gateway Timeout`: Request timeout

---

### 3. Reserve Zone Slot
Reserve a fishing slot in a zone and increment slots_filled.

**Endpoint:**
```
POST /api/zones/{hex_id}/reserve
```

**Path Parameters:**
- `hex_id` (required): The hexagonal zone identifier

**Request Body (JSON):**
```json
{
  "fisher_id": "fisher_123",
  "time_window": "full_day"
}
```

**Body Parameters:**
- `fisher_id` (required): Unique identifier for the fisher
- `time_window` (required): Booking window - one of: "morning", "full_day", "overnight"

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/zones/hex_001/reserve" \
  -H "Content-Type: application/json" \
  -d '{
    "fisher_id": "fisher_123",
    "time_window": "full_day"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "status": "reserved",
  "zone": "hex_001",
  "fisher": "fisher_123",
  "window": "full_day",
  "confirmation": "RES-hex_001-1705324560",
  "slots_filled": 16,
  "slots_total": 20
}
```

**Error Responses:**
- `400 Bad Request`: Invalid fisher_id or time_window
- `404 Not Found`: Zone not found
- `409 Conflict`: No slots available in zone
- `500 Internal Server Error`: Unexpected error
- `503 Service Unavailable`: Database connection failed
- `504 Gateway Timeout`: Request timeout

---

### 4. Create Logbook Entry
Create a new fishing logbook entry (catch record).

**Endpoint:**
```
POST /api/logbook
```

**Request Body (JSON):**
```json
{
  "fisher_id": "fisher_123",
  "zone_id": "hex_001",
  "timestamp": "2024-01-15T14:30:00Z",
  "species_caught": [
    {
      "name": "plaice",
      "weight_kg": 2.5
    },
    {
      "name": "sole",
      "weight_kg": 1.2
    }
  ],
  "total_kg": 3.7,
  "notes": "Good catch despite rough seas"
}
```

**Body Parameters:**
- `fisher_id` (required): Unique identifier for the fisher
- `zone_id` (required): Hexagonal zone identifier where fishing occurred
- `timestamp` (optional): ISO 8601 timestamp (defaults to current time)
- `species_caught` (optional): Array of species objects with name and weight
- `total_kg` (optional): Total catch weight in kilograms
- `notes` (optional): Additional notes about the catch

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/logbook" \
  -H "Content-Type: application/json" \
  -d '{
    "fisher_id": "fisher_123",
    "zone_id": "hex_001",
    "species_caught": [{"name": "plaice", "weight_kg": 2.5}],
    "total_kg": 2.5
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Logbook entry created successfully",
  "entry": {
    "id": 42,
    "fisher_id": "fisher_123",
    "zone_id": "hex_001",
    "timestamp": "2024-01-15T14:30:00Z",
    "species_caught": [
      {
        "name": "plaice",
        "weight_kg": 2.5
      }
    ],
    "total_kg": 2.5
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Unexpected error
- `503 Service Unavailable`: Database connection failed
- `504 Gateway Timeout`: Request timeout

---

### 5. Get All Ports
Fetch all available fishing ports.

**Endpoint:**
```
GET /api/ports
```

**Query Parameters:** None

**Example Request:**
```bash
curl "http://localhost:8000/api/ports"
```

**Response (200 OK):**
```json
{
  "success": true,
  "ports": [
    {
      "id": 1,
      "name": "IJmuiden",
      "lat": 52.4545,
      "lon": 4.5486
    },
    {
      "id": 2,
      "name": "Scheveningen",
      "lat": 52.0997,
      "lon": 4.2678
    },
    {
      "id": 3,
      "name": "Urk",
      "lat": 52.6617,
      "lon": 5.5891
    }
  ],
  "count": 3
}
```

**Error Responses:**
- `401 Unauthorized`: Authentication failed with Supabase
- `403 Forbidden`: Access denied to ports table
- `500 Internal Server Error`: Unexpected error
- `503 Service Unavailable`: Database connection failed
- `504 Gateway Timeout`: Request timeout

---

## CORS Configuration
The API is configured to accept requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:8000` (API server)
- `https://*.vercel.app` (Vercel deployments)
- `https://*.netlify.app` (Netlify deployments)

## Error Handling
The API implements comprehensive error handling:

- **Authentication Errors (401)**: Supabase API key is invalid or missing
- **Authorization Errors (403)**: Insufficient permissions to access the zones table
- **Validation Errors (400)**: Invalid request parameters
- **Not Found Errors (404)**: Requested resource does not exist
- **Connection Errors (503)**: Cannot reach the Supabase database
- **Timeout Errors (504)**: Database query took too long
- **Server Errors (500)**: Unexpected internal server errors

All errors include descriptive messages to help with debugging.

## Logging
The API logs all requests and errors to help with monitoring and debugging. Logs include:
- Request details
- Response status codes
- Database query times
- Error stack traces

## Performance Tips
1. Use `limit` parameter to fetch only needed records
2. Use `sortby` to get most relevant results first
3. Use `offset` for pagination rather than fetching all records
4. Filter by `species` when looking for specific fish types
5. Set appropriate `timeout` values when making requests

## Environment Setup
Create a `.env` file in the backend directory:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_or_service_role_key
```

## Running the API
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py

# Access interactive docs
http://localhost:8000/docs
```

## API Documentation Interface
FastAPI provides an interactive API documentation interface at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
