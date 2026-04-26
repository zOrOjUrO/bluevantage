import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import json
import os
import numpy as np
import base64

# --- Page Config ---
st.set_page_config(page_title="BlueVantage", layout="wide", page_icon="🎣")

# --- Enhanced CSS with BlueVantage color palette and icons ---
st.markdown("""
<style>
    /* BlueVantage Color Palette */
    :root {
        --primary-blue: #0066cc;
        --ocean-blue: #0048a3;
        --accent-teal: #00a8cc;
        --success-green: #2ecc71;
        --warning-orange: #ff9500;
        --danger-red: #ef4444;
        --light-bg: #f0f7ff;
        --dark-bg: #0d1b2a;
    }
    
    .block-container { padding: 3.5rem 1rem; max-width: 100%; }
    .stMetric { font-size: 0.75rem; }
    div[data-testid="stMetricValue"] { font-size: 1rem; line-height: 1.2; color: #0066cc; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.65rem; color: #666; }
    .stWarning { padding: 0.5rem 1rem; margin-bottom: 0.5rem; font-size: 0.8rem; background: #fff7ed; border-left: 4px solid #ff9500; }
    .stCaption { font-size: 0.65rem; margin-top: 0; padding-top: 0; }
    .stSelectbox label { font-size: 0.75rem; font-weight: 600; color: #0048a3; }
    .stSlider label { font-size: 0.75rem; font-weight: 600; color: #0048a3; }
    section[data-testid="stSidebar"] .block-container { padding: 1rem 0.8rem; background: linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%); }
    section[data-testid="stSidebar"] .stSlider label { font-size: 0.75rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem; }
    .stPlotlyChart { margin-top: -0.5rem; }
    
    /* Slider accent color - BlueVantage blue */
    div[data-testid="stThumbValue"] { background: #0066cc !important; }
    
    /* Header styling - prominent */
    .header-container {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
        padding: 16px;
        background: linear-gradient(135deg, #0048a3 0%, #0066cc 100%);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.15);
    }
    .header-logo {
        width: 60px;
        height: 60px;
        flex-shrink: 0;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }
    .header-text h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        padding: 0;
        line-height: 1.1;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .header-text p {
        font-size: 0.95rem;
        color: #e0f2fe;
        margin: 0;
        padding: 0;
        line-height: 1.3;
    }
    
    /* Legend styling */
    .legend-container {
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 8px 0;
    }
    .legend-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #0048a3;
        margin-bottom: 8px;
    }
    .legend-gradient {
        width: 100%;
        height: 30px;
        background: linear-gradient(to right, #ff9500, #ffc107, #2ecc71, #00a8cc);
        border-radius: 4px;
        border: 1px solid #ddd;
        margin-bottom: 6px;
    }
    .legend-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: #666;
        font-weight: 600;
    }
    
    /* Footer styling */
    .footer-container {
        background: #0d1b2a;
        color: #a0aec0;
        padding: 16px;
        border-radius: 8px;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 16px;
        line-height: 1.6;
    }
    .footer-container a {
        color: #0066cc;
        text-decoration: none;
        font-weight: 600;
    }
    .footer-container a:hover {
        text-decoration: underline;
    }
    
    /* About popup button */
    .about-button {
        background: #0066cc;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
    }
    .about-button:hover {
        background: #0048a3;
    }
    
    /* Section divider */
    .section-divider {
        border-bottom: 2px solid #e0f2fe;
        margin: 12px 0;
    }
    
    /* Sidebar header with icon */
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #0048a3;
        margin-bottom: 8px;
    }
    
    /* Map caption with legend */
    .map-legend-text {
        font-size: 0.75rem;
        color: #666;
        padding: 8px;
        background: #f9fafb;
        border-radius: 4px;
        border-left: 3px solid #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data(filepath="data/zones.json"):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    
    df = pd.DataFrame(data)
    for col in df.select_dtypes(include=['float64', 'float32']).columns:
        df[col] = df[col].round(2)
    
    def get_dominant(row):
        if not row: return 'N/A'
        return sorted(row, key=lambda x: x['prob'], reverse=True)[0]['name']
    
    df['top_species'] = df['species'].apply(get_dominant)
    return df

# --- Load data ---
df = load_data()
if df is None:
    uploaded = st.sidebar.file_uploader("Upload JSON", type=['json'])
    if uploaded:
        data = json.load(uploaded)
        df = pd.DataFrame(data)
        for col in df.select_dtypes(include=['float64', 'float32']).columns:
            df[col] = df[col].round(2)
        df['top_species'] = df['species'].apply(
            lambda r: sorted(r, key=lambda x: x['prob'], reverse=True)[0]['name'] if r else 'N/A'
        )
    else:
        st.stop()

all_species = sorted(list(set(s['name'] for spec in df['species'] for s in spec)))

# ============================================================
# SIDEBAR - IMPROVED WITH ICONS
# ============================================================
st.sidebar.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-header">⚙️ Trip Settings</div>', unsafe_allow_html=True)

selected_species = st.sidebar.selectbox(
    "🐟 Target Species", ['All'] + all_species,
    index=all_species.index('Plaice') + 1 if 'Plaice' in all_species else 0
)

max_distance = st.sidebar.slider(
    "📍 Max Distance (km)", 
    10, 300, 100, 10,
    help="Maximum distance from Urk Harbor"
)

max_waves = st.sidebar.slider(
    "🌊 Max Wave Height (m)", 
    0.5, 5.0, 3.0, 0.5,
    help="Maximum acceptable wave height for safe fishing"
)

min_score = st.sidebar.slider(
    "📊 Min Zone Score", 
    0, 100, 50, 5,
    help="Minimum predicted catch probability (0-100)"
)

yield_min, yield_max = st.sidebar.slider(
    "🎣 Expected Yield (kg)", 
    0.0, 100.0, (0.0, 100.0), 1.0,
    help="Expected catch range per fishing trip"
)

st.sidebar.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-header">🗺️ Map Style</div>', unsafe_allow_html=True)
basemap_choice = st.sidebar.radio("Basemap", ["Light", "Satellite"], horizontal=True)

# About popup
st.sidebar.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
if st.sidebar.button("ℹ️ About BlueVantage", use_container_width=True):
    st.session_state.show_about = not st.session_state.get('show_about', False)

if st.session_state.get('show_about', False):
    st.sidebar.markdown("""
    ### About BlueVantage
    
    **Informed Fishery Intelligence** 🌊
    
    BlueVantage is an intelligent fishing zone prediction system that uses 
    advanced machine learning and real-time environmental data to identify 
    optimal fishing locations in the North Sea, centered around Urk Harbor.
    
    **Data Sources:**
    - 🐠 ICES DATRAS: Historical catch records
    - 🌡️ Copernicus Marine: SST & Chlorophyll data
    - 📏 EMODnet: Bathymetry & MPA boundaries
    - 🤖 ML Model: XGBoost classifier
    
    **Species Tracked:**
    Plaice • Sole • Cod • Herring • Mackerel
    
    **Developed for:** CASSINI Hackathon 2026
    """)


# ============================================================
# FILTERING
# ============================================================
mpa = df[df['is_mpa'] == True]
fishable = df[df['is_mpa'] == False]

fishable = fishable[
    (fishable['distance_km'] <= max_distance) &
    (fishable['wave_height_m'] <= max_waves) &
    (fishable['zone_score'] >= min_score) &
    (fishable['yield_high_kg'] >= yield_min) &
    (fishable['yield_low_kg'] <= yield_max)
]

mpa_in_range = mpa[mpa['distance_km'] <= max_distance]

if selected_species != 'All' and not fishable.empty:
    def species_match(row, target):
        for s in row:
            if s['name'] == target: return s['prob']
        return 0
    fishable = fishable.copy()
    fishable['match'] = fishable['species'].apply(lambda r: species_match(r, selected_species))
    fishable = fishable[fishable['match'] > 0]
    fishable = fishable.sort_values('match', ascending=False)

# ============================================================
# ORANGE-TO-GREEN COLOR SCALE
# ============================================================
def build_color_scale(filtered_df):
    if filtered_df.empty:
        return lambda s: [128, 128, 128]
    vmin = filtered_df['zone_score'].min()
    vmax = filtered_df['zone_score'].max()
    if vmax == vmin:
        return lambda s: [0, 200, 83]
    def color_fn(score):
        t = (score - vmin) / (vmax - vmin)
        t = max(0, min(1, t))
        r = int(255 * (1 - t))
        g = int(140 + t * 60)
        b = int(t * 83)
        return [r, g, b]
    return color_fn

color_fn = build_color_scale(fishable)
fishable['color'] = fishable['zone_score'].apply(color_fn)
fishable['status_text'] = 'Fishable'
mpa_in_range['status_text'] = 'MPA – PROHIBITED'

# ============================================================
# HEADER: Logo + Title + Subtitle with Prominent Styling
# ============================================================

logo_path = "logo.png"

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<div class="header-container">'
        f'<img src="data:image/png;base64,{logo_b64}" class="header-logo">'
        f'<div class="header-text"><h1>BlueVantage</h1><p>🌊 Informed Fishery Intelligence • Optimal Fishing Zone Predictions</p></div>'
        f'</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="header-container">'
        '<div style="font-size:50px;width:60px;height:60px;text-align:center;line-height:60px;">🎣</div>'
        '<div class="header-text"><h1>BlueVantage</h1><p>🌊 Informed Fishery Intelligence • Optimal Fishing Zone Predictions</p></div>'
        '</div>',
        unsafe_allow_html=True
    )

# ============================================================
# CONTINUOUS COLOR SCALE LEGEND
# ============================================================
if not fishable.empty:
    vmin = fishable['zone_score'].min()
    vmax = fishable['zone_score'].max()
    st.markdown(
        f"""
        <div class="legend-container">
            <div class="legend-title">🎯 Zone Score Scale</div>
            <div class="legend-gradient"></div>
            <div class="legend-labels">
                <span>{vmin:.0f} (Low)</span>
                <span>{(vmin + vmax) / 2:.0f} (Medium)</span>
                <span>{vmax:.0f} (High)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# MPA warning
if len(mpa_in_range) > 0:
    st.warning(f"🚫 {len(mpa_in_range)} MPA zone(s) in range – NO FISHING ALLOWED", icon="🚫")


# Metrics row - with icons
m1, m2, m3, m4 = st.columns(4)
m1.metric("🗺️ Available Zones", len(fishable))
m2.metric("🎣 Avg Yield", 
    f"{fishable['yield_low_kg'].mean():.0f}–{fishable['yield_high_kg'].mean():.0f} kg"
    if not fishable.empty else "—")
m3.metric("📊 Avg Score", f"{fishable['zone_score'].mean():.0f}/100" if not fishable.empty else "—")
m4.metric("📍 Free Slots", f"{5 - int(fishable['slots_filled'].mean())}/5" if not fishable.empty else "—")

# Map + Details
col_map, col_detail = st.columns([3, 2])

selected_lat = None
selected_lng = None

with col_detail:
    st.subheader("🎯 Zone Details")
    
    if not fishable.empty:
        if selected_species != 'All':
            labels = fishable.apply(
                lambda r: f"🐟 {r['lat']:.2f}, {r['lng']:.2f} – {selected_species}: {r['match']:.0%}", 
                axis=1
            ).tolist()
        else:
            labels = fishable.apply(
                lambda r: f"📍 {r['lat']:.2f}, {r['lng']:.2f} – Score: {r['zone_score']:.0f}", 
                axis=1
            ).tolist()
        
        choice = st.selectbox("Select zone", labels, index=0, label_visibility="collapsed")
        zone = fishable.iloc[labels.index(choice)]
        selected_lat = zone['lat']
        selected_lng = zone['lng']
        
        c1, c2 = st.columns(2)
        c1.metric("📊 Score", f"{zone['zone_score']:.0f}/100", delta=f"vs avg {fishable['zone_score'].mean():.0f}")
        c1.metric("📍 Distance", f"{zone['distance_km']:.0f} km")
        c2.metric("🎣 Expected Yield", f"{zone['yield_low_kg']:.0f}–{zone['yield_high_kg']:.0f} kg")
        c2.metric("🅿️ Free Slots", f"{5 - int(zone['slots_filled'])}/5")
        
        st.caption(f"🌊 Wave Height: {zone['wave_height_m']} m | 🧊 Water Depth: {zone.get('depth_m', '—')} m")
        
        st.markdown("**Species Distribution:**")
        spec_df = pd.DataFrame(zone['species']).set_index('name').sort_values('prob', ascending=False)
        bar_colors = ['#0066cc' if s == selected_species else '#cbd5e1' for s in spec_df.index]
        fig = px.bar(spec_df, y=spec_df.index, x='prob', orientation='h')
        fig.update_traces(marker_color=bar_colors)
        fig.update_layout(
            height=140, margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Catch Probability", yaxis_title=None, 
            xaxis_visible=True,
            plot_bgcolor='rgba(240, 247, 255, 0.5)'
        )
        fig.update_xaxes(showticklabels=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("📭 No matching zones found. Adjust your filters.")

with col_map:
    layers = []
    
    # Satellite tile layer (free, no API key)
    if basemap_choice == "Satellite":
        layers.append(pdk.Layer(
            "TileLayer",
            data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            min_zoom=0,
            max_zoom=19,
            tile_size=256,
        ))
    
    # MPA layer
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        mpa_in_range,
        get_position='[lng, lat]',
        get_fill_color='[239, 68, 68, 200]',
        get_line_color='[248, 113, 113, 255]',
        get_line_width=3,
        get_radius=1200,
        pickable=True,
    ))
    
    # Fishable zones (orange-green gradient)
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        fishable,
        get_position='[lng, lat]',
        get_fill_color='color',
        get_radius=1000,
        pickable=True,
    ))
    
    # Score labels on points
    fishable_copy = fishable.copy()
    fishable_copy['score_label'] = fishable_copy['zone_score'].astype(str)
    layers.append(pdk.Layer(
        "TextLayer",
        fishable_copy,
        get_position='[lng, lat]',
        get_text='score_label',
        get_size=14,
        get_color='[255, 255, 255, 255]',
        get_angle=0,
        get_text_anchor='"middle"',
        get_alignment_baseline='"center"',
        pickable=False,
    ))
    
    # Highlight selected zone
    if selected_lat is not None:
        highlight = pd.DataFrame([{'lat': selected_lat, 'lng': selected_lng}])
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            highlight,
            get_position='[lng, lat]',
            get_fill_color='[255, 255, 255, 40]',
            get_line_color='[255, 255, 255, 255]',
            get_line_width=5,
            get_radius=1600,
            pickable=False,
        ))
    
    view = pdk.ViewState(
        latitude=selected_lat if selected_lat else 52.662,
        longitude=selected_lng if selected_lng else 5.601,
        zoom=8, pitch=45,
        height=250
    )
    
    st.pydeck_chart(pdk.Deck(
        layers=layers,
        initial_view_state=view,
        height=350,
        map_style=None if basemap_choice == "Satellite" else "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={
            "html": """
                <b>Zone Coordinates:</b> {lat}, {lng}<br>
                <b>Status:</b> {status_text}<br>
                <b>Score:</b> {zone_score}/100 | <b>Yield:</b> {yield_low_kg}–{yield_high_kg} kg<br>
                <b>🌊 Waves:</b> {wave_height_m}m | <b>📍 Distance:</b> {distance_km} km
            """,
            "style": {"backgroundColor": "#0d1b2a", "color": "#e0f2fe", "padding": "10px", "fontFamily": "sans-serif", "fontSize": "12px"}
        }
    ))

# Enhanced legend
st.markdown(
    '<div class="map-legend-text">'
    '🟠 Low Score – 🟡 Medium – 🟢 High Score | 🔴 MPA (Protected Zone) | ⭕ Selected Zone'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# FOOTER WITH PROJECT INFORMATION
# ============================================================
st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer-container">
    <strong>🌊 BlueVantage – Informed Fishery Intelligence</strong><br>
    Intelligent fishing zone predictions using ML + environmental data<br><br>
    </div>
""", unsafe_allow_html=True)
