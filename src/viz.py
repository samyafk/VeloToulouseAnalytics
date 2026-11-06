import pandas as pd
from pathlib import Path
import streamlit as st
import duckdb
from utils import get_env_var
from dotenv import load_dotenv

load_dotenv()

WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))

# Create a read-only connection to the db
duckdb_conn = duckdb.connect(
    WAREHOUSE_DIR / "VeloToulouseAnalytics.db",
    read_only=True
)

snapshot_timestamp = '2026-11-06T20:14:00.000Z'

latest_snapshot = duckdb_conn.sql(f"""
    SELECT name, lat, lon, last_updated
    FROM stations_history
    WHERE last_updated = '{snapshot_timestamp}'
""").df()

df = pd.DataFrame(
    latest_snapshot,
    columns=["lat", "lon"],
)

st.map(df, alt=f"Snapshot VeloToulouse at {snapshot_timestamp}")