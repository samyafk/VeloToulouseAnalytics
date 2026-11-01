import oci
from os import listdir
from os.path import isfile, join
from urllib.request import urlretrieve
from utils import get_env_var
from dotenv import load_dotenv

load_dotenv()  # reads .env


BUCKET_NAME = get_env_var("OCI_BUCKET")
RAW_DATA_FOLDER = get_env_var("RAW_DATA_DIR")
SNAPSHOTS_FOLDER = get_env_var("SNAPSHOTS_DATA_DIR")
METADATA_URL = get_env_var("STATIONS_METADATA_URL")

# Load config (use profile_name="OTHER" if you have a non-default profile)
config = oci.config.from_file("~/.oci/config", "DEFAULT")
oci.config.validate_config(config)  # raises if the config is malformed

client = oci.object_storage.ObjectStorageClient(config)
namespace = client.get_namespace().data

print("====================sync-snapshots====================")

print(f"Fetching objects from bucket : '{BUCKET_NAME}'")

# list_call_get_all_results follows pagination automatically
response = oci.pagination.list_call_get_all_results(
    client.list_objects,
    namespace,
    BUCKET_NAME,
    fields="name",
)

objects = response.data.objects
print(f"Found {len(objects)} objects\n")

objects_names = [obj.name for obj in objects]

old_files = [f for f in listdir(SNAPSHOTS_FOLDER) if isfile(join(SNAPSHOTS_FOLDER, f))]

# Missing files
new_files = list(set(objects_names) - set(old_files))
print(f"{len(new_files)} new files to be downloaded")

# Download the missing files
for file_name in new_files:
    response = client.get_object(namespace, BUCKET_NAME, file_name)
    with open(SNAPSHOTS_FOLDER + file_name, "wb") as f:
        f.write(response.data.content)

print("Snapshot were successfully synchronized!")
print("======================================================\n")

print("====================sync-metadata====================")

metadata_path = RAW_DATA_FOLDER + 'stations-metadata.parquet'
urlretrieve(METADATA_URL, metadata_path)

print("Stations metadata was successfully synchronized!")
print("=====================================================")

