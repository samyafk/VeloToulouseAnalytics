import html
from pathlib import Path

import branca
import duckdb
import folium
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium


from velotoulouse.preprocess.clean import preprocess
from velotoulouse.utils import get_env_var


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------

load_dotenv()

ASSETS_DIR = Path(get_env_var("ASSETS_DIR"))
CLEAN_DATA_DIR = Path(get_env_var("CLEAN_DATA_DIR"))
SNAPSHOT_PATH = CLEAN_DATA_DIR / "latest_snapshot_processed.parquet"

REPAIR_WORKSHOP_STATION_ID = 1031  # City bike repair workshop, not a real station
MAX_BUBBLE_SIZE = 80.0
RADIUS_FACTOR = 1.5  # Circle radius (meters) = size * factor

MAP_ZOOM_START = 13
MAP_ZOOM_MAX = 18

CARTO_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
)

PAGE_CSS = """
<style>
  .block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
  }
</style>
"""


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------


@st.cache_data(ttl=60, show_spinner="Refreshing latest snapshot...")
def load_latest_snapshot():
    """Sync the latest snapshot, then load it with a bubble `size` per station.

    Cached for 60s, so changing a filter doesn't re-run the sync or the query.
    """
    preprocess(clean_history=False, sync_latest_snapshot=True)

    query = f"""
        WITH snapshot AS (
            SELECT
                *, 
                MAX(capacity) OVER () AS max_capacity,
                MIN(capacity) OVER () AS min_capacity
            FROM read_parquet('{SNAPSHOT_PATH}', union_by_name = true)
            WHERE station_id != {REPAIR_WORKSHOP_STATION_ID}
        )
        SELECT
            *,
            {MAX_BUBBLE_SIZE} / NULLIF(max_capacity - min_capacity, 0) * capacity AS size
        FROM snapshot
    """
    with duckdb.connect() as conn:
        df = conn.execute(query).df()

    # NULLIF yields NULL when all capacities are equal: fall back to a mid-size bubble
    df["size"] = df["size"].fillna(MAX_BUBBLE_SIZE / 2)
    return df


def filter_stations(df, filters):
    """Apply the selected filters. If nothing is selected, return the entire dataframe"""
    names = filters["selected_stations"]
    hide_empty_stations = filters["hide_empty_stations"]
    hide_full_stations = filters["hide_full_stations"]

    # Station selection
    df_f = df[df["name"].isin(names)] if names else df

    # Hide empty stations
    if hide_empty_stations:
        df_f = df_f[df_f["num_bikes_available"] != 0]
    
    # Hide full stations
    if hide_full_stations:
        df_f = df_f[df_f["num_docks_available"] != 0]
    
    return df_f


# ----------------------------------------------------------------------------
# Map
# ----------------------------------------------------------------------------


def add_base_tiles(m):
    """Add CARTO dark tiles if an API key is set in .streamlit/secrets.toml."""
    try:
        carto_key = st.secrets["CARTO_API_KEY"]
    except (KeyError, FileNotFoundError):
        # Default OSM tiles stay in place
        return

    folium.TileLayer(
        tiles=f"https://basemaps.cartocdn.com/rastertiles/dark_all/{{z}}/{{x}}/{{y}}.png?key={carto_key}",
        attr=CARTO_ATTRIBUTION,
        name="CARTO Dark Matter",
    ).add_to(m)


def build_popup(row) -> folium.Popup:
    content = f"""
        <h1>{html.escape(str(row["name"]))}</h1>
        <p>
            Time : {row["last_updated"]}<br>
            Mechanical bikes available : {row["num_mechanical"]}<br>
            Electrical bikes available : {row["num_electrical"]}<br>
            Parking slots available : {row["num_docks_available"]}
        </p>
    """
    iframe = branca.element.IFrame(html=content, width=300, height=200)
    return folium.Popup(iframe, max_width=500)


def add_station_markers(m, df):
    for row in df.itertuples(index=False):
        row = pd.Series(row._asdict())
        folium.Circle(
            location=[row["lat"], row["lon"]],
            radius=RADIUS_FACTOR * row["size"],
            weight=0,
            fill=True,
            fill_color="#f87e16",
            fill_opacity=0.5,
            tooltip=row["name"],
            popup=build_popup(row),
        ).add_to(m)


def build_map(df):


    

    if df.empty: # Toulouse center coordinates
        center = [43.6047, 1.4442]
    else:
        center = [df["lat"].mean(), df["lon"].mean()]

    m = folium.Map(
        location=center,
        max_zoom=MAP_ZOOM_MAX,
        zoom_start=MAP_ZOOM_START,
        zoom_control=False,
    )

    m.fit_bounds(
        [[df["lat"].min(), df["lon"].min()], [df["lat"].max(), df["lon"].max()]],
        padding=(40, 40)
    )

    add_base_tiles(m)
    add_station_markers(m, df)

    return m


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------


def render_sidebar(df):
    with st.sidebar:
        st.image(ASSETS_DIR / "favicon.png", width=250)
        st.caption("Real-time bike availability")
        selected_stations = st.multiselect(
            "Stations",
            sorted(df["name"].unique()),
            placeholder="All stations",
        )
        hide_empty_stations = st.toggle("Hide empty stations")
        hide_full_stations = st.toggle("Hide full stations")
        return {
            "selected_stations" : selected_stations,
            "hide_empty_stations" : hide_empty_stations,
            "hide_full_stations" : hide_full_stations
        }


def main():
    # Must be the first Streamlit call
    st.set_page_config(
        page_title="VeloToulouseAnalytics",
        page_icon=ASSETS_DIR / "favicon.png",
        initial_sidebar_state="collapsed",
        menu_items=None,
        layout="wide",
    )
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    df = load_latest_snapshot()
    filters = render_sidebar(df)
    df_filtered = filter_stations(df, filters)

    with st.spinner("Loading..."):
        st_folium(build_map(df_filtered), use_container_width=True, height=650, returned_objects=[])


main()