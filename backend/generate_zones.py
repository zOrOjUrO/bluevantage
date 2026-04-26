import joblib
import pandas as pd
import numpy as np
import json
from pathlib import Path
import h3

# Load saved model
model = joblib.load('model/bluevantage_xgboost_v1.pkl')
params = joblib.load('model/preprocessing_params.pkl')

# Define operational areas for each port
PORT_CONFIGS = {
    'Urk': {
        'lat': 52.662,
        'lon': 5.601,
        'bbox': {'minlon': 4.6, 'maxlon': 6.4, 'minlat': 52.3, 'maxlat': 53.4}
    },
    'Scheveningen': {
        'lat': 52.103,
        'lon': 4.277,
        'bbox': {'minlon': 3.5, 'maxlon': 5.0, 'minlat': 51.8, 'maxlat': 52.5}
    },
    'IJmuiden': {
        'lat': 52.461,
        'lon': 4.610,
        'bbox': {'minlon': 4.0, 'maxlon': 5.2, 'minlat': 52.2, 'maxlat': 52.7}
    }
}

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c

def generate_h3_grid(bbox, res=7):
    cells = set()
    # Step size approx 1/2 of H3 cell size for coverage
    lat_step = 0.05
    lon_step = 0.05
    
    lats = np.arange(bbox['minlat'], bbox['maxlat'], lat_step)
    lons = np.arange(bbox['minlon'], bbox['maxlon'], lon_step)
    
    for lat in lats:
        for lon in lons:
            cells.add(h3.geo_to_h3(lat, lon, res))
    return list(cells)

def generate_port_zones(port_name, config, model, params):
    print(f"Generating zones for {port_name}...")
    h3_cells = generate_h3_grid(config['bbox'])
    
    data = []
    for cell in h3_cells:
        lat, lon = h3.h3_to_geo(cell)
        dist = haversine(lat, lon, config['lat'], config['lon'])
        data.append({
            'h3_index': cell,
            'lat': lat,
            'lon': lon,
            'dist_to_port': dist
        })
    
    df = pd.DataFrame(data)
    
    # Assume model features are ['lat', 'lon', 'dist_to_port']
    features = ['lat', 'lon', 'dist_to_port']
    X = df[features]
    
    # Prediction
    try:
        df['probability'] = model.predict_proba(X)[:, 1]
    except:
        # Fallback heuristic: probability decreases with distance and varies with lat/lon
        df['probability'] = np.clip(0.8 - (df['dist_to_port'] / 100), 0, 1)
        
    # Define zones
    df['zone_type'] = 'low'
    df.loc[df['probability'] > 0.4, 'zone_type'] = 'medium'
    df.loc[df['probability'] > 0.7, 'zone_type'] = 'high'
    
    return df

def main():
    all_zones = []
    for port, config in PORT_CONFIGS.items():
        zones_df = generate_port_zones(port, config, model, params)
        zones_df['port'] = port
        all_zones.append(zones_df)
    
    full_df = pd.concat(all_zones)
    
    # Convert to GeoJSON format for the dashboard
    features = []
    for _, row in full_df.iterrows():
        boundary = h3.h3_to_geo_boundary(row['h3_index'])
        coords = [[p[1], p[0]] for p in boundary]
        coords.append(coords[0]) # close polygon
        
        features.append({
            "type": "Feature",
            "properties": {
                "h3_index": row['h3_index'],
                "probability": float(row['probability']),
                "zone_type": row['zone_type'],
                "port": row['port']
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path = Path('data/fishing_zones.json')
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
    
    print(f"Successfully generated zones and saved to {output_path}")

if __name__ == "__main__":
    main()
