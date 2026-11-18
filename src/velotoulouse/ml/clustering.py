from pathlib import Path
import duckdb
from dotenv import load_dotenv
from urllib.request import urlretrieve
import os

from velotoulouse.const import (
    FINAL_SCHEMA,
    NULL_TO_VAL_COLS,
    STATIONS_HISTORY_COLUMNS,
    STATIONS_METADATA_COLUMNS,
)
from velotoulouse.utils import (
    get_env_var,
    get_clustering_query
)


def clustering():
    
    load_dotenv()
    WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))
    OUTPUT_PATH = Path(get_env_var("CLEAN_DATA_DIR")) / "clustering.parquet"

    QUERY = get_clustering_query()

    con = duckdb.connect(WAREHOUSE_DIR / "VeloToulouseAnalytics.db", read_only=True)
    try:
        table_name = "stations_clustering"
        con.execute(f"CREATE TEMP TABLE {table_name} AS {QUERY}")
        con.execute(f"COPY {table_name} TO '{OUTPUT_PATH}' (FORMAT parquet)")
    finally:
        con.close()



if __name__ == "__main__":
    clustering()