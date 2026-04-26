import os
import requests
import pandas as pd
import io
from pathlib import Path

DATRAS_BASE = "https://datras.ices.dk/WebServices/DATRASWebService.asmx"
DATA_DIR = Path("data")

def fetch_datras_table(table_name: str, survey: str, year: int, quarter: int):
    endpoint = f"get{table_name}data"
    url = f"{DATRAS_BASE}/{endpoint}"
    params = {"survey": survey, "year": year, "quarter": quarter}
    
    print(f"Fetching {table_name} for {survey} {year} Q{quarter}...")
    resp = requests.get(url, params=params, timeout=120)
    resp.raise_for_status()
    
    ns = {"d": "ices.dk.local/DATRAS"}
    row_tag = f"Cls_DatrasExchange_{table_name}"
    
    try:
        df = pd.read_xml(io.BytesIO(resp.content), xpath=f".//d:{row_tag}", namespaces=ns)
        return df
    except Exception as e:
        print(f"Failed to parse XML: {e}")
        return None

def download_ices_data(years=[2024], quarters=[1], survey="NS-IBTS"):
    hh_frames = []
    hl_frames = []
    
    for year in years:
        for quarter in quarters:
            df_hh = fetch_datras_table("HH", survey, year, quarter)
            df_hl = fetch_datras_table("HL", survey, year, quarter)
            
            if df_hh is not None: hh_frames.append(df_hh)
            if df_hl is not None: hl_frames.append(df_hl)
            
    if not hh_frames or not hl_frames:
        print("No data retrieved from ICES.")
        return
        
    pd.concat(hh_frames, ignore_index=True).to_csv(DATA_DIR / "HH.csv", index=False)
    pd.concat(hl_frames, ignore_index=True).to_csv(DATA_DIR / "HL.csv", index=False)
    print(f"Saved ICES data to {DATA_DIR}")

if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    download_ices_data()
