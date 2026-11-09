import pandas as pd
from pathlib import Path
import streamlit as st
import folium
from streamlit_folium import st_folium
import duckdb
from velotoulouse.utils import get_env_var
from dotenv import load_dotenv
import branca


load_dotenv()

WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))

# Create a read-only connection to the db
duckdb_conn = duckdb.connect(
    WAREHOUSE_DIR / "VeloToulouseAnalytics.db",
    read_only=True
)

latest_snapshot = duckdb_conn.sql(f"""
    with SNAPSHOT AS (
        SELECT 
            *,
            MAX(capacity) OVER () AS max_capacity,
            MIN(capacity) OVER () AS min_capacity,
            MAX(last_updated) OVER () AS latest_snapshot_time
        FROM stations_history
        WHERE
            station_id != 1031 -- This is the city bike repair workshop station
    )
    SELECT
        *,
        ((80.0 / (max_capacity - min_capacity)) * capacity) AS size
    FROM SNAPSHOT
    WHERE
        last_updated = latest_snapshot_time
    
""").df()

df = pd.DataFrame(latest_snapshot)

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
            Time : {row["latest_snapshot_time"]}<br>
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

st_folium(m, width=725, returned_objects=[])