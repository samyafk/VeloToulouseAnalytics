import duckdb
from utils import get_env_var
from dotenv import load_dotenv

# Loading env variables
load_dotenv()  # reads .env

BUCKET_NAME = get_env_var("OCI_BUCKET")
SNAPSHOTS_FOLDER = get_env_var("SNAPSHOTS_DATA_DIR")
CLEAN_FOLDER = get_env_var("CLEAN_DATA_DIR")
WAREHOUSE_FOLDER = get_env_var("WAREHOUSE_DIR")

# Create/connect to db file
con = duckdb.connect(WAREHOUSE_FOLDER + "VeloToulouseAnalytics.db")

con.sql(f"""
    SELECT *
    FROM read_parquet('{SNAPSHOTS_FOLDER}/*.parquet',
                        union_by_name = true)
""").show()


