# BlueVantage: Informed Fishery Intelligence

![BlueVantage Logo](logo.png)

## Project Overview

**BlueVantage** is an intelligent fishing zone prediction system that uses advanced machine learning and real-time environmental data to identify optimal fishing locations in the North Sea, specifically centered around **Urk Harbor** in the Netherlands.

Developed for the **CASSINI Hackathon 2026**, BlueVantage supports sustainable fishing by providing data-driven insights into fish distribution and optimal fishing zones.

---

## Architecture Overview

BlueVantage is a full-stack application with three layers:

```
┌─────────────────────────────────────────────┐
│           Frontend (Vite / React)            │
│   Mapbox GL · H3-js · Real-time Hex Map      │
└───────────────────┬─────────────────────────┘
                    │ REST API
┌───────────────────▼─────────────────────────┐
│           Backend (FastAPI / Python)         │
│   XGBoost Model · Supabase · Telegram Bot    │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│        ML Pipeline (Jupyter Notebook)        │
│   ICES DATRAS · Copernicus · EMODnet         │
└─────────────────────────────────────────────┘
```

---

## Repository Structure

```
bluevantage/
├── README.md
├── logo.png
├── frontend/                        # Vite/React app
│   ├── package.json
│   └── src/
├── backend/                         # FastAPI server + XGBoost model
│   ├── main.py
│   ├── requirements.txt
│   └── zones.json                   # Pre-generated zone predictions
├── model/                           # ML pipeline
│   └── prediction_engine_urk.ipynb
└── dataset/                         # Raw data (generated at runtime)
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Node.js 18+
- [Copernicus Marine account](https://marine.copernicus.eu/) *(for running the ML pipeline)*

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# API running at http://localhost:8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

### Environment Variables

Create a `.env` file in `backend/`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Create a `.env` file in `frontend/`:

```env
VITE_MAPBOX_TOKEN=your_mapbox_token
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

> **Tip**: Copy `.env.example` in each directory to get started. Never commit `.env` files.

---

## ☁️ Cloud Deployment

### Backend (Railway / Render)

1. Link your GitHub repo and set the root directory to `backend`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables: `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`

### Frontend (Vercel)

1. Link your GitHub repo, set framework to **Vite**, root directory to `frontend`
2. Add environment variables: `VITE_MAPBOX_TOKEN`, `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

---

## Running the ML Pipeline

The prediction engine lives in `model/prediction_engine_urk.ipynb` and generates the `zones.json` consumed by the backend.

```bash
python -m jupyter notebook model/prediction_engine_urk.ipynb
```

Authenticate when prompted:

```
COPERNICUSMARINE_SERVICE_USERNAME: <your-email>
COPERNICUSMARINE_SERVICE_PASSWORD: <your-password>
```

### Pipeline Steps

1. **Environment Setup** — Install packages and configure paths
2. **Download ICES DATRAS Data** — Historical haul and catch records
3. **Fetch Copernicus Marine Data** — SST and Chlorophyll (2018–2024)
4. **EMODnet Integration** — Bathymetry and MPA boundaries
5. **H3 Hex Grid Generation** — Hexagonal spatial grid at resolution 6
6. **Spatial Join** — Aggregate all features to hex cells
7. **Model Training** — XGBoost classifier on historical CPUE data
8. **Prediction & Ranking** — Score all operational zones
9. **Export** — Write `zones.json` to `backend/`

---

## 🌐 API Reference

Base URL: `http://localhost:8000` (Supabase)[https://tnapfawdehztxsqmoeyy.supabase.co]

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/zones` | All zone predictions |
| `GET` | `/api/zones?limit=10` | Paginated zones |
| `GET` | `/api/zones/{hex_id}` | Single zone by hex ID |

Interactive docs: [`/docs`](http://localhost:8000/docs) (Swagger UI) · [`/redoc`](http://localhost:8000/redoc)

### Zone Object

```json
{
  "hex_id": "8625cd...",
  "lat": 52.8,
  "lon": 5.3,
  "sst_celsius": 12.5,
  "chl_mg_m3": 1.2,
  "depth_m": 25.5,
  "is_mpa": false,
  "probability": 0.75,
  "rank": 1
}
```

---

## 🔧 Model Details

**Algorithm**: XGBoost Classifier (binary: high-catch probability)
**Training data**: ICES DATRAS hauls 2018–2024, North Sea
**Operational area**: 52.3°–53.4°N, 4.6°–6.4°E (center: Urk Harbor 52.662°N, 5.601°E)
**Grid resolution**: H3 level 6 (~1.5 km² per cell), ~100+ zones

### Features

| Category | Features |
|----------|----------|
| Spatial | Lat/lon, distance from Urk (km), H3 ID, depth (m) |
| Environmental | SST (°C), Chlorophyll (mg/m³), MPA status |
| Temporal | Season week, historical CPUE (normalized 0–1) |

**Species tracked**: Plaice, Sole, Cod, Herring, Mackerel

---

## 📚 Data Sources

| Source | Type | Coverage | Frequency |
|--------|------|----------|-----------|
| [ICES DATRAS](https://datras.ices.dk/WebServices/) | Historical catch | 2018–2024 | Annual |
| [Copernicus Marine](https://marine.copernicus.eu/) | SST / Chlorophyll | Monthly | Near-real-time |
| [EMODnet](https://emodnet.ec.europa.eu/) | Bathymetry / MPAs | Static | Annual |

---

## 🎓 Key Concepts

**H3 Hexagonal Grid**: Uber's H3 at resolution 6 provides ~1.5 km² cells for consistent spatial aggregation of catch and environmental data.

**CPUE (Catch Per Unit Effort)**: Derived from ICES hauls and normalized 0–1 to represent historical zone productivity. Used as the primary training signal.

**Fail-fast mode**: The pipeline requires real data from all sources — it will not proceed if any critical source is unavailable.

---

## 🔜 Roadmap

- [x] Live XGBoost model integration
- [x] Real-time H3 hexagon map (Mapbox)
- [ ] Automated weekly data refresh (Copernicus / ICES via GitHub Actions)
- [ ] Expanded port support (Den Helder, IJmuiden, Scheveningen)
- [ ] Telegram bot alerts for high-probability zones
- [ ] Species-specific prediction layers
- [ ] Mobile app integration

---

## 🤝 Contributing

Contributions are welcome. Areas for enhancement: additional species models, real-time data integration, forecast modeling with weather data, performance optimization, and extended operational areas.

Please open an issue before submitting a PR for large changes.

---

## 👥 Credits

Developed for **CASSINI Hackathon 2026**

**Data Partners:**
- [ICES](https://www.ices.dk) — International Council for the Exploration of the Sea
- [Copernicus Marine Service](https://marine.copernicus.eu/)
- [EMODnet](https://emodnet.ec.europa.eu/) — European Marine Observation and Data Network

## 📄 License

The MIT License (MIT)

Copyright (c) 2011-2026 The Bootstrap Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

---

*Last updated: April 2026*
