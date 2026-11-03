STATIONS_HISTORY_COLUMNS = [
    "num_bikes_available",
    "num_bikes_disabled",
    "num_docks_available",
    "num_docks_disabled",
    "is_installed",
    "is_renting",
    "is_returnin AS is_returning",
    "last_reported",
    "station_id",
    "last_updated",
    "version",
]

STATIONS_METADATA_COLUMNS = [
    "station_id",
    "name",
    "capacity",
    "address",
    "rental_methods",
    "lat",
    "lon"
]

NULL_TO_VAL_COLS = {
    "num_bikes_available": 0,
    "num_bikes_disabled": 0,
    "num_docks_available": 0,
    "num_docks_disabled": 0
}

FINAL_SCHEMA = { # Col: type
    "id" : "VARCHAR",
    "station_id" : "INTEGER",
    "last_updated" : "TIMESTAMP",
    "last_reported" : "TIMESTAMP",
    "name" : "VARCHAR",
    "capacity" : "INTEGER",
    "num_mechanical" : "INTEGER",
    "num_electrical" : "INTEGER",
    "num_bikes_available" : "INTEGER",
    "num_bikes_disabled" : "INTEGER",
    "num_docks_available" : "INTEGER",
    "num_docks_disabled" : "INTEGER",
    "is_installed" : "BOOLEAN",
    "is_renting" : "BOOLEAN",
    "is_returning" : "BOOLEAN",
    "credit_card_accepted" : "BOOLEAN",
    "address" : "VARCHAR",
    "lat" : "DOUBLE",
    "lon" : "DOUBLE",
    "version" : "VARCHAR",
}