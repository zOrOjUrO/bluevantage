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

def compute_zone_score(zone, fisher_target='plaice'):
    """
    Your zone scoring formula from the master plan
    """
    species_match = zone.get(f'p{fisher_target}', 0)
    yield_score = zone['yieldkgmean'] / 700  # Normalize
    weather_score = max(0, 1 - (zone['waveheightm'] / 4.0) - (zone['windkmh'] / 80.0))
    cpue_score = zone['historicalcpue']
    distance_penalty = zone['distancekm'] / 150  # Max distance
    
    score = (
        0.35 * species_match +
        0.25 * yield_score +
        0.20 * weather_score +
        0.15 * cpue_score -
        0.05 * distance_penalty
    ) * 100
    
    if zone['ismpa']:
        return 0
    
    return round(max(0, min(100, score)), 1)

def generate_zones_for_port(port_name, port_lat, port_lon, bbox):
    """
    Generate zones for a specific port
    
    Args:
        port_name: e.g., "Urk", "Scheveningen", "IJmuiden"
        port_lat, port_lon: Home port coordinates
        bbox: {'minlon': x, 'maxlon': x, 'minlat': x, 'maxlat': x}
    """
    
    print(f"Generating zones for {port_name}...")
    
    # 1. Generate H3 hexagons (fast - no API calls)
    from shapely.geometry import Polygon
    bbox_coords = [
        (bbox['minlon'], bbox['minlat']),
        (bbox['maxlon'], bbox['minlat']),
        (bbox['maxlon'], bbox['maxlat']),
        (bbox['minlon'], bbox['maxlat']),
        (bbox['minlon'], bbox['minlat']),
    ]
    
    geojson_polygon = {"type": "Polygon", "coordinates": [bbox_coords]}
    hexids = list(h3.polyfill(geojson_polygon, res=6, geo_json_conformant=True))
    
    print(f"  → {len(hexids)} hexagons generated")
    
    # 2. Load cached environmental data (instead of re-downloading)
    # You should save this from your notebook once
    try:
        dfenv = pd.read_csv('data/environmental_data_cached.csv')
        dfdepth = pd.read_csv('data/bathymetry_cached.csv')
        print(f"  → Loaded cached environmental data")
    except FileNotFoundError:
        print("  ⚠️  No cached data found. Run full notebook first to generate cache.")
        return []
    
    # 3. Prepare features for each hex
    hex_features = []
    for hex_id in hexids:
        lat, lon = h3.h3_to_geo(hex_id)
        
        # Get nearest environmental data (using cached data)
        env_nearest = dfenv.iloc[
            ((dfenv['lat'] - lat)**2 + (dfenv['lon'] - lon)**2).argmin()
        ]
        depth_nearest = dfdepth.iloc[
            ((dfdepth['lat'] - lat)**2 + (dfdepth['lon'] - lon)**2).argmin()
        ] if not dfdepth.empty else {'depthm': 30}
        
        features = {
            'hexid': hex_id,
            'lat': lat,
            'lon': lon,
            'sstcelsius': env_nearest['sstcelsius'],
            'chlmgm3': env_nearest['chlmgm3'],
            'depthm': depth_nearest['depthm'],
            'seasonweek': 17,  # Current week (update dynamically)
            'distancekm': haversine(lat, lon, port_lat, port_lon),
            'historicalcpue': 0.5,  # Default - update with real data
            'ismpa': False  # Update with real MPA check
        }
        hex_features.append(features)
    
    dfhex = pd.DataFrame(hex_features)
    
    # 4. Run model predictions (FAST - no retraining)
    X = dfhex[[
        'sstcelsius', 'chlmgm3', 'depthm', 'seasonweek',
        'distancekm', 'historicalcpue'
    ]]
    
    predictions = model.predict(X)  # Shape: (n_hexes, 5 species)
    
    # 5. Build zones output
    zones = []
    species_records = []
    species_names = ['plaice', 'sole', 'cod', 'herring', 'mackerel']
    
    for idx, row in dfhex.iterrows():
        # Normalize predictions to probabilities
        pred_sum = predictions[idx].sum()
        if pred_sum > 0:
            probs = predictions[idx] / pred_sum
        else:
            probs = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        
        # Estimate yield from predictions
        total_yield = predictions[idx].sum()
        yield_low = max(0, int(total_yield * 0.7))
        yield_high = int(total_yield * 1.3)
        
        zone_data = {
            'hexid': row['hexid'],
            'lat': row['lat'],
            'lon': row['lon'],
            'yieldkgmean': total_yield,
            'waveheightm': 1.5,  # TODO: Get from Open-Meteo
            'windkmh': 20,       # TODO: Get from Open-Meteo
            'ismpa': row['ismpa'],
            'distancekm': row['distancekm'],
            'historicalcpue': row['historicalcpue']
        }
        
        # Add species probabilities for scoring
        for i, sp_name in enumerate(species_names):
            zone_data[f'p{sp_name}'] = probs[i]
        
        # Compute zone score
        zone_score = compute_zone_score(zone_data)
        
        zones.append({
            'hex_id': row['hexid'],
            'lat': float(row['lat']),
            'lng': float(row['lon']),
            'zone_score': zone_score,
            'yield_low_kg': yield_low,
            'yield_high_kg': yield_high,
            'slots_total': 5,
            'slots_filled': 0,
            'wave_height_m': 1.5,
            'wind_kmh': 20,
            'is_mpa': bool(row['ismpa']),
            'distance_km': float(row['distancekm']),
            'port': port_name
        })
        
        # Species breakdown for zone_species table
        for i, sp_name in enumerate(species_names):
            species_records.append({
                'hex_id': row['hexid'],
                'species_name': sp_name.capitalize(),
                'probability': float(probs[i])
            })
    
    print(f"  ✓ Generated {len(zones)} zones for {port_name}")
    
    return zones, species_records

# Example usage:
if __name__ == "__main__":
    
    # Generate zones for all ports
    all_zones = []
    all_species = []

    for port_name, config in PORT_CONFIGS.items():
        zones, species = generate_zones_for_port(
            port_name=port_name,
            port_lat=config['lat'],
            port_lon=config['lon'],
            bbox=config['bbox']
        )
    all_zones.extend(zones)
    all_species.extend(species)
    
    # Export
    with open('data/zones_for_supabase.json', 'w') as f:
        json.dump(all_zones, f, indent=2)
    
    with open('data/zone_species_for_supabase.json', 'w') as f:
        json.dump(all_species, f, indent=2)
    
    print(f"\n✅ Exported {len(all_zones)} zones across all ports")