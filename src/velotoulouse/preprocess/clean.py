from pathlib import Path
import duckdb
from dotenv import load_dotenv
from urllib.request import urlretrieve


from velotoulouse.const import (
    FINAL_SCHEMA,
    NULL_TO_VAL_COLS,
    STATIONS_HISTORY_COLUMNS,
    STATIONS_METADATA_COLUMNS,
)
from velotoulouse.utils import (
    get_env_var,
    run_checks,
    get_preprocess_query
)

def preprocess(clean_history=True, sync_latest_snapshot=False):
    
    load_dotenv()
    METADATA_DIR = Path(get_env_var("METADATA_DIR"))

    if clean_history:

        SNAPSHOTS_DIR = Path(get_env_var("SNAPSHOTS_DATA_DIR"))
        WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))
        OUTPUT_PATH = Path(get_env_var("CLEAN_DATA_DIR")) / "stations_history.parquet"

        QUERY = get_preprocess_query(
            STATIONS_HISTORY_COLUMNS,
            STATIONS_METADATA_COLUMNS,
            NULL_TO_VAL_COLS,
            FINAL_SCHEMA,
            SNAPSHOTS_DIR,
            METADATA_DIR
        )

        table_name = "stations_history"
        con = duckdb.connect(WAREHOUSE_DIR / "VeloToulouseAnalytics.db")
        try:
            con.sql(f"CREATE OR REPLACE TABLE {table_name} AS {QUERY}")
            run_checks(con, table_name)  # data quality checks go here, before writing
            con.sql(f"COPY {table_name} TO '{OUTPUT_PATH}' (FORMAT parquet)")
        finally:
            con.close()

    if sync_latest_snapshot:

        LATEST_SNAPSHOT_URL = get_env_var("LATEST_SNAPSHOT_URL")
        LATEST_SNAPSHOT_DIR = Path(get_env_var("LATEST_SNAPSHOT_DIR"))
        OUTPUT_PATH = Path(get_env_var("CLEAN_DATA_DIR")) / "stations_history.parquet"

        QUERY = get_preprocess_query(
            STATIONS_HISTORY_COLUMNS,
            STATIONS_METADATA_COLUMNS,
            NULL_TO_VAL_COLS,
            FINAL_SCHEMA,
            LATEST_SNAPSHOT_DIR,
            METADATA_DIR
        )

        urlretrieve(LATEST_SNAPSHOT_URL, LATEST_SNAPSHOT_DIR / 'latest-snapshot.parquet')
        
        con = duckdb.connect()
        try:
            table_name = "stations_latest_snapshot"
            con.sql(f"CREATE TEMP TABLE {table_name} AS {QUERY}")
            run_checks(con, table_name)  # data quality checks go here, before writing
            con.sql(f"COPY {table_name} TO '{OUTPUT_PATH}' (FORMAT parquet)")
        finally:
            con.close()



if __name__ == "__main__":
    preprocess(clean_history=False, sync_latest_snapshot=True)