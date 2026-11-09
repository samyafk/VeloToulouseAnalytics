from pathlib import Path
import duckdb
from dotenv import load_dotenv

from velotoulouse.const import (
    FINAL_SCHEMA,
    NULL_TO_VAL_COLS,
    STATIONS_HISTORY_COLUMNS,
    STATIONS_METADATA_COLUMNS,
)
from velotoulouse.utils import (
    get_env_var,
    run_checks
)

load_dotenv()

RAW_DIR = Path(get_env_var("RAW_DATA_DIR"))
SNAPSHOTS_DIR = Path(get_env_var("SNAPSHOTS_DATA_DIR"))
CLEAN_DIR = Path(get_env_var("CLEAN_DATA_DIR"))
WAREHOUSE_DIR = Path(get_env_var("WAREHOUSE_DIR"))
OUTPUT_PATH = CLEAN_DIR / "stations_history.parquet"

# Useful to extract mechanical and eletrical bike count from struct column 'data'
VEHICLE_TYPES_SCHEMA = (
    '{"vehicle_types_available": [{"vehicle_type_id": "VARCHAR", "count": "INTEGER"}]}'
)

# Relevant columns to keep
HISTORY_COLS = ", ".join(STATIONS_HISTORY_COLUMNS)
METADATA_COLS = ", ".join(STATIONS_METADATA_COLUMNS)

# Fill null values with 0
NULL_FILLS = ",\n            ".join(
    f"COALESCE({col}, {value}) AS {col}" for col, value in NULL_TO_VAL_COLS.items()
)

# Fill null names and addresses
NULL_FILLS += """
    ,\n            COALESCE(address, 'STATION ADDRESS UNAVAILABLE') AS address
"""

# Final schema with strict type
FINAL_SELECT = ",\n        ".join(
    f"{col}::{dtype} AS {col}" for col, dtype in FINAL_SCHEMA.items()
)

QUERY = f"""
    WITH parsed AS ( -- extract vehicle_types_available from data column
        SELECT
            *,
            json_transform(data, '{VEHICLE_TYPES_SCHEMA}').vehicle_types_available AS vehicle_types
        FROM read_parquet('{SNAPSHOTS_DIR}/*.parquet', union_by_name = true)
    ),
    history AS ( -- create primary_key, extracts mechanical and eletrical bike count & drops duplicates
        SELECT
            CONCAT(station_id, '_', last_updated) AS id,
            list_filter(vehicle_types, lambda v : v.vehicle_type_id == 'mechanical')[1]['count'] AS num_mechanical,
            list_filter(vehicle_types, lambda v : v.vehicle_type_id == 'electrical')[1]['count'] AS num_electrical,
            {HISTORY_COLS}
        FROM parsed
        QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, last_updated) = 1
    ),
    metadata AS ( -- load stations metadata
        SELECT {METADATA_COLS}
        FROM read_parquet('{RAW_DIR}/stations-metadata.parquet', union_by_name = true)
    ),
    joined AS ( -- add stations metadata to the table
        SELECT h.*, m.* EXCLUDE (station_id)
        FROM history AS h
        LEFT JOIN metadata AS m ON h.station_id = m.station_id
    ),
    flagged AS (
        -- flags first: they must see the NULLs before they are filled
        SELECT *, (rental_methods IS NOT NULL) AS credit_card_accepted
        FROM joined
    ),
    casted AS (
        SELECT * REPLACE ( -- cast boolean columns
            CAST(capacity AS INTEGER) AS capacity,
            CAST(is_installed AS BOOLEAN) AS is_installed,
            CAST(is_renting AS BOOLEAN) AS is_renting,
            CAST(is_returning AS BOOLEAN) AS is_returning,
        )
        FROM flagged
    ),
    cleaned AS (
        SELECT * REPLACE ( -- replace null values with 0 for some columns + cast epoch to Timestamp
            (to_timestamp(last_reported) AT TIME ZONE 'UTC') AS last_reported,
            (to_timestamp(last_updated) AT TIME ZONE 'UTC') AS last_updated,
            {NULL_FILLS}
        )
        FROM casted
    )
    SELECT
        {FINAL_SELECT}
    FROM cleaned
    WHERE -- Here we can put some cleaning filters
        last_reported > TIMESTAMP '2026-01-01' AND
        num_mechanical >= 0 AND
        num_electrical >= 0
"""


def main() -> None:
    con = duckdb.connect(WAREHOUSE_DIR / "VeloToulouseAnalytics.db")
    try:
        con.sql(f"CREATE OR REPLACE TABLE stations_history AS {QUERY}")
        run_checks(con)  # data quality checks go here, before writing
        con.sql(f"COPY stations_history TO '{OUTPUT_PATH}' (FORMAT parquet)")
    finally:
        con.close()


if __name__ == "__main__":
    main()