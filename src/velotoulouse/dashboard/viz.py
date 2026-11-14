import pandas as pd
from pathlib import Path
import streamlit as st
import folium
from streamlit_folium import st_folium
import duckdb
from velotoulouse.utils import get_env_var
from dotenv import load_dotenv
import branca
from velotoulouse.preprocess.clean import preprocess


############################################## Fetch data for the latest timestamp ##############################################

load_dotenv()
WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))
ASSETS_DIR = Path(get_env_var("ASSETS_DIR"))
CLEAN_DATA_DIR = Path(get_env_var("CLEAN_DATA_DIR"))

# Refresh latest snapshot
preprocess(clean_history=False, sync_latest_snapshot=True)

# Create a in memory db con
duckdb_conn = duckdb.connect()

latest_snapshot = duckdb_conn.sql(f"""
    with SNAPSHOT AS (
        SELECT 
            *,
            MAX(capacity) OVER () AS max_capacity,
            MIN(capacity) OVER () AS min_capacity
        FROM read_parquet('{CLEAN_DATA_DIR / "latest_snapshot_processed.parquet"}', union_by_name = true)
        WHERE
            station_id != 1031 -- This is the city bike repair workshop station
    )
    SELECT
        *,
        ((80.0 / (max_capacity - min_capacity)) * capacity) AS size
    FROM SNAPSHOT
    
""").df()

df = pd.DataFrame(latest_snapshot)


############################################## Dashboard setup ##############################################

# Create the map object
m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=13, max_zoom=18)

# Use CARTO dark tile if an API key is provided in .streamlit/secrets.toml
try:
    CARTO_KEY = st.secrets["CARTO_API_KEY"]
    folium.TileLayer(
        tiles=f"https://basemaps.cartocdn.com/rastertiles/dark_all/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="CARTO Dark Matter"
    ).add_to(m)
except:
    print("No API key is provided in .streamlit/secrets.toml. Default OSM tile will be used.")

# Add all the stations to the map
for _, row in df.iterrows():

    # HTML for Iframe popup
    html = f"""
        <h1>{row["name"]}</h1>
        <p>
            Time : {row["last_updated"]}<br>
            Mechanical bikes available : {row["num_mechanical"]}<br>
            Electrical bikes available : {row["num_electrical"]}<br>
            Parking slots available : {row["num_docks_available"]}
        </p>
        """

    iframe = branca.element.IFrame(html=html, width=300, height=200)
    popup = folium.Popup(iframe, max_width=500)

    folium.Circle(
        location=[row["lat"], row["lon"]],
        radius= 1.5 * row["size"],          # radius in meters
        color="red",
        weight=0,
        fill=True,
        fill_color="#f87e16",
        fill_opacity=0.4,
        tooltip=row["name"],
        popup=popup
    ).add_to(m)


# Page setup
st.set_page_config(page_title= "VeloToulouseAnalytics", page_icon=ASSETS_DIR / "favicon.png", initial_sidebar_state=None, menu_items=None, layout="wide")

# Title
st.header('VeloToulouse Analytics dashboard', anchor=False)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3rem;
            padding-bottom: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        iframe[title="streamlit_folium.st_folium"] {
            height: calc(100vh - 200px) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)



with st.spinner("Loading data..."):
    map_data = st_folium(m, use_container_width=True, returned_objects=[])
