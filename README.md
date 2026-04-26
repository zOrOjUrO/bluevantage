# BlueVantage: Informed Fishery Intelligence

![BlueVantage Logo](logo.png)

## 🎯 Project Overview

**BlueVantage** is an intelligent fishing zone prediction system that uses advanced machine learning and real-time environmental data to identify optimal fishing locations in the North Sea, specifically centered around **Urk Harbor** in the Netherlands.

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Start the Backend API
```bash
cd backend
pip install -r requirements.txt
python main.py
```
API will be running on `http://localhost:8000`.

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend will be running on `http://localhost:5173`.

## ☁️ Cloud Deployment

### 1. Backend (Railway / Render)
1. Link your GitHub repo.
2. Set the root directory to `backend`.
3. Set the build command: `pip install -r requirements.txt`.
4. Set the start command: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Add Environment Variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `TELEGRAM_BOT_TOKEN`

### 2. Frontend (Vercel)
1. Link your GitHub repo.
2. Set the framework to **Vite**.
3. Set the root directory to `frontend`.
4. Add Environment Variables:
   - `VITE_MAPBOX_TOKEN`
   - `VITE_API_URL` (Point this to your deployed backend URL)
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`

## 🔜 Roadmap
- [x] Live XGBoost Model Integration
- [x] Real-time H3 Hexagon Map
- [ ] Automated Weekly Data Refresh (Copernicus/ICES)
- [ ] Expanded Port Support (Den Helder, IJmuiden)
