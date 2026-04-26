# BlueVantage API Endpoints Summary

## Complete API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| **GET** | `/api/zones` | Get all zones with optional filtering (species, sorting, pagination) |
| **GET** | `/api/zones/{hex_id}` | Get single zone details |
| **POST** | `/api/zones/{hex_id}/reserve` | Reserve a fishing slot (increments slots_filled) |
| **POST** | `/api/logbook` | Create a new logbook/catch entry |
| **GET** | `/api/ports` | Get list of all fishing ports |

---

## Endpoint Details

### 1. GET /api/zones
**Purpose:** Returns all zones with species joined

**Query Parameters:**
- `species` (optional): Filter by species name
- `limit` (optional, default: 100): Max results (1-1000)
- `offset` (optional, default: 0): Pagination offset
- `sortby` (optional): Sort field (zonescore, windkmh, waveheightm, distancekm)

**Response Example:**
```json
{
  "success": true,
  "zones": [
    {
      "hexid": "hex_001",
      "lat": 52.52,
      "lon": 13.40,
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

---

### 2. GET /api/zones/{hex_id}
**Purpose:** Single zone detail

**Path Parameters:**
- `hex_id` (required): Zone hexagonal identifier

**Response Example:**
```json
{
  "success": true,
  "zone": {
    "hexid": "hex_001",
    "lat": 52.52,
    "lon": 13.40,
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

---

### 3. POST /api/zones/{hex_id}/reserve
**Purpose:** Increment slots_filled to reserve a slot

**Path Parameters:**
- `hex_id` (required): Zone hexagonal identifier

**Request Body:**
```json
{
  "fisher_id": "fisher_123",
  "time_window": "full_day"
}
```

**Response Example:**
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

**Error (409 Conflict) - No slots available:**
```json
{
  "detail": "No slots available in zone hex_001"
}
```

---

### 4. POST /api/logbook
**Purpose:** Insert into logbook_entries table

**Request Body:**
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

**Response Example:**
```json
{
  "success": true,
  "message": "Logbook entry created successfully",
  "entry": {
    "fisher_id": "fisher_123",
    "zone_id": "hex_001"
  }
}
```

---

### 5. GET /api/ports
**Purpose:** List all ports (for port filtering)

**Query Parameters:** None

**Response Example:**
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

---

## Error Handling

All endpoints return appropriate HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | ✅ Success |
| 201 | ✅ Created |
| 400 | ❌ Bad Request (validation error) |
| 401 | ❌ Unauthorized (auth failed) |
| 403 | ❌ Forbidden (access denied) |
| 404 | ❌ Not Found |
| 409 | ❌ Conflict (no slots available) |
| 500 | ❌ Internal Server Error |
| 503 | ❌ Service Unavailable (DB offline) |
| 504 | ❌ Gateway Timeout (DB slow) |

---

## Testing the API

### Using curl:
```bash
# Get all zones
curl http://localhost:8000/api/zones

# Get specific zone
curl http://localhost:8000/api/zones/hex_001

# Reserve a slot
curl -X POST http://localhost:8000/api/zones/hex_001/reserve \
  -H "Content-Type: application/json" \
  -d '{"fisher_id": "fisher_123", "time_window": "full_day"}'

# Create logbook entry
curl -X POST http://localhost:8000/api/logbook \
  -H "Content-Type: application/json" \
  -d '{"fisher_id": "fisher_123", "zone_id": "hex_001", "total_kg": 2.5}'

# Get ports
curl http://localhost:8000/api/ports
```

### Using interactive API docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Implementation Status

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /api/zones | ✅ Complete | Filters, sorts, paginates |
| GET /api/zones/{hex_id} | ✅ Complete | Returns full zone data |
| POST /api/zones/{hex_id}/reserve | ✅ Complete | Updates slots_filled in DB |
| POST /api/logbook | ✅ Complete | Inserts into logbook_entries |
| GET /api/ports | ✅ Complete | Returns ports list |

All endpoints include:
- ✅ Full error handling
- ✅ Proper logging
- ✅ CORS support
- ✅ Request validation
- ✅ Timeout protection
