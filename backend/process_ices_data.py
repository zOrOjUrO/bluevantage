import pandas as pd
from pathlib import Path
import h3

DATA_DIR = Path("data")

def process_ices_data():
    hh_path = DATA_DIR / "HH.csv"
    hl_path = DATA_DIR / "HL.csv"
    
    if not hh_path.exists() or not hl_path.exists():
        print("Raw ICES data files not found. Run fetch_ices_data.py first.")
        return

    print("Loading ICES data...")
    df_hh = pd.read_csv(hh_path)
    df_hl = pd.read_csv(hl_path)

    # Merge HL with HH to get coordinates
    # We use ShootLat and ShootLong for the location of the haul
    df = pd.merge(df_hl, df_hh[['HaulID', 'ShootLat', 'ShootLong', 'Year', 'Quarter']], on='HaulID')

    # Convert lat/lon to H3 hexagons (resolution 6)
    df['h3_index'] = df.apply(lambda row: h3.geo_to_h3(row['ShootLat'], row['ShootLong'], 6), axis=1)

    # Aggregate by hexagon and time to calculate historical abundance
    summary = df.groupby(['h3_index']).agg({
        'TotalNo': 'mean'
    }).reset_index()

    summary.rename(columns={'TotalNo': 'historical_abundance'}, inplace=True)

    output_path = DATA_DIR / "ices_processed_summary.csv"
    summary.to_csv(output_path, index=False)
    print(f"Processed ICES data saved to {output_path}")

if __name__ == "__main__":
    process_ices_data()
