import duckdb
from utils import get_env_var
from dotenv import load_dotenv
from const import STATIONS_HISTORY_COLUMNS
from const import STATIONS_METADATA_COLUMNS

# Loading env variables
load_dotenv()  # reads .env

BUCKET_NAME = get_env_var("OCI_BUCKET")
RAW_FOLDER = get_env_var("RAW_DATA_DIR")
SNAPSHOTS_FOLDER = get_env_var("SNAPSHOTS_DATA_DIR")
CLEAN_FOLDER = get_env_var("CLEAN_DATA_DIR")
WAREHOUSE_FOLDER = get_env_var("WAREHOUSE_DIR")

# Create/connect to db file
con = duckdb.connect(WAREHOUSE_FOLDER + "VeloToulouseAnalytics.db")

# Load all the raw snapshot parquet files and creates/replaces the table stations_history
con.sql(f"""
    CREATE OR REPLACE TABLE stations_history AS
    SELECT * FROM read_parquet('{SNAPSHOTS_FOLDER}/*.parquet', union_by_name = true)
""")

# Load the stations metadata file and creates/replaces the table stations_metadata
con.sql(f"""
    CREATE OR REPLACE TABLE stations_metadata AS
    SELECT * FROM read_parquet('{RAW_FOLDER}/stations-metadata.parquet', union_by_name = true)
""")

# Preview stations_metadata
con.sql("SELECT * FROM stations_metadata").show()

# Remove duplicate and create primary key <station_id>_<last_updated>
con.sql(f"""
    CREATE OR REPLACE TABLE stations_history AS
    SELECT
        CONCAT(station_id, '_', last_updated) AS id,
        JSON_VALUE(data, '$.vehicle_types_available[0].count') AS num_mechanical,
        JSON_VALUE(data, '$.vehicle_types_available[1].count') AS num_electrical,
        {", ".join(STATIONS_HISTORY_COLUMNS)}
    FROM stations_history
    QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, last_updated) = 1
""")


con.sql(f"""
    CREATE OR REPLACE TABLE stations_history AS
    SELECT h.*, m.* EXCLUDE (station_id)
    FROM stations_history AS h
    LEFT JOIN (
        SELECT {", ".join(STATIONS_METADATA_COLUMNS)} FROM stations_metadata
    ) AS m
    ON h.station_id=m.station_id
""")
# Store data into the clean parquet file
con.sql(f"COPY (SELECT * FROM stations_history) TO '{CLEAN_FOLDER}/stations_history.parquet' (FORMAT parquet)").show()




