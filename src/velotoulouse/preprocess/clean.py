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
    check_no_duplicates,
    get_preprocess_query,
    move_to_folder
)

def preprocess(clean_history=True, sync_latest_snapshot=False):
    
    load_dotenv()
    METADATA_DIR = Path(get_env_var("METADATA_DIR"))

    if clean_history:

        NEW_SNAPSHOTS_DIR = Path(get_env_var("SNAPSHOTS_DATA_DIR")) / 'new/'
        OLD_SNAPSHOTS_DIR = Path(get_env_var("SNAPSHOTS_DATA_DIR")) / 'old/'
        WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))
        OUTPUT_PATH = Path(get_env_var("CLEAN_DATA_DIR")) / "stations_history.parquet"

        QUERY = get_preprocess_query(
            STATIONS_HISTORY_COLUMNS,
            STATIONS_METADATA_COLUMNS,
            NULL_TO_VAL_COLS,
            FINAL_SCHEMA,
            NEW_SNAPSHOTS_DIR,
            METADATA_DIR
        )

        table_name = "stations_history"
        con = duckdb.connect(WAREHOUSE_DIR / "VeloToulouseAnalytics.db")
        STAGING = f"{table_name}__staging"

        try:
            con.execute(f"CREATE OR REPLACE TEMP TABLE {STAGING} AS {QUERY}")
            run_checks(con, STAGING)
            check_no_duplicates(con, STAGING, table_name)

            con.execute("BEGIN TRANSACTION")
            con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM {STAGING} LIMIT 0")
            con.execute(f"INSERT INTO {table_name} SELECT * FROM {STAGING}")
            con.execute(f"COPY {table_name} TO '{OUTPUT_PATH}' (FORMAT parquet)")
            con.execute("COMMIT")

            move_to_folder(NEW_SNAPSHOTS_DIR, OLD_SNAPSHOTS_DIR)
        except Exception:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            raise
        finally:
            con.execute(f"DROP TABLE IF EXISTS {STAGING}")
            con.close()

    if sync_latest_snapshot:

        LATEST_SNAPSHOT_URL = get_env_var("LATEST_SNAPSHOT_URL")
        RAW_LATEST_SNAPSHOT_DIR = Path(get_env_var("RAW_LATEST_SNAPSHOT_DIR"))
        OUTPUT_PATH = Path(get_env_var("CLEAN_DATA_DIR")) / "latest_snapshot_processed.parquet"

        QUERY = get_preprocess_query(
            STATIONS_HISTORY_COLUMNS,
            STATIONS_METADATA_COLUMNS,
            NULL_TO_VAL_COLS,
            FINAL_SCHEMA,
            RAW_LATEST_SNAPSHOT_DIR,
            METADATA_DIR
        )

        urlretrieve(LATEST_SNAPSHOT_URL, RAW_LATEST_SNAPSHOT_DIR / 'latest_snapshot_raw.parquet')
        
        con = duckdb.connect()
        try:
            table_name = "stations_latest_snapshot"
            con.sql(f"CREATE TEMP TABLE {table_name} AS {QUERY}")
            run_checks(con, table_name)  # data quality checks go here, before writing
            con.sql(f"COPY {table_name} TO '{OUTPUT_PATH}' (FORMAT parquet)")
        finally:
            con.close()



if __name__ == "__main__":
    preprocess()