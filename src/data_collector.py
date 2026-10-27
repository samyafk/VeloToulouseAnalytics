from urllib.request import urlretrieve
import datetime as dt

# Get actual time
now = dt.datetime.now(dt.timezone.utc)

# Convert datetime object to YYYY-MM-DD HH:MM:SS
now_str = now.strftime("%Y-%m-%d %H:%M:%S")

# Create file name string
file_name = "../data/raw/snapshot_" + now_str + ".parquet"

# Toulouse-Metropole API Endpoint
URL = "https://data.toulouse-metropole.fr/api/explore/v2.1/catalog/datasets/velotoulouse-disponibilite-temps-reel/exports/parquet?lang=fr&timezone=Europe%2FBerlin"

# GET Snapshot and save result in /data/raw folder
urlretrieve(URL, file_name)

