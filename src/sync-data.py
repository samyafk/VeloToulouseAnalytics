import oci
from os import listdir
from os.path import isfile, join
from urllib.request import urlretrieve

BUCKET_NAME = "VeloToulouse-snapshots"

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

# Get the list of already downloaded files 
data_folder = '/home/samyafk/VeloToulouseAnalytics/data/raw/'
snapshots_path = data_folder + 'snapshots/'

old_files = [f for f in listdir(snapshots_path) if isfile(join(snapshots_path, f))]

# Missing files
new_files = list(set(objects_names) - set(old_files))
print(f"{len(new_files)} new files to be downloaded")

# Download the missing files
for file_name in new_files:
    response = client.get_object(namespace, BUCKET_NAME, file_name)
    with open(snapshots_path + file_name, "wb") as f:
        f.write(response.data.content)

print("Snapshot were successfully synchronized!")
print("======================================================\n")

print("====================sync-metadata====================")

METADATA_URL = "https://data.toulouse-metropole.fr/api/explore/v2.1/catalog/datasets/velotoulouse-localisation-et-caracteristique-des-stations/exports/parquet?lang=fr&timezone=Europe%2FBerlin"
metadata_path = data_folder + 'stations-metadata.parquet'
urlretrieve(METADATA_URL, metadata_path)

print("Stations metadata was successfully synchronized!")
print("=====================================================")

