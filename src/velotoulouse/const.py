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
    "num_docks_disabled": 0,
    "capacity": 0,
    "is_installed": False,
    "is_renting": False,
    "is_returning": False
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

CHECKS = {
    "primary key (id) is unique": """
        SELECT COUNT(*) - COUNT(DISTINCT id) FROM stations_history
    """,
    "no NULL keys": """
        SELECT COUNT(*) FROM stations_history
        WHERE station_id IS NULL OR last_updated IS NULL
    """,
    "station coordinates are not null": """
        SELECT COUNT(*) FROM stations_history WHERE lat IS NULL OR lon IS NULL
    """,
    "station flags are not null": """
        SELECT COUNT(*) FROM stations_history WHERE is_installed IS NULL OR is_renting IS NULL OR is_returning IS NULL
    """,
    "capacity is not null or negative": """
        SELECT COUNT(*) FROM stations_history
        WHERE capacity IS NULL OR capacity < 0
    """,
    "num_mechanical is not null or negative": """
        SELECT COUNT(*) FROM stations_history
        WHERE num_mechanical IS NULL OR num_mechanical < 0
    """,
    "num_electrical is not null or negative": """
        SELECT COUNT(*) FROM stations_history
        WHERE num_electrical IS NULL OR num_electrical < 0
    """,
    "mechanical + electrical = total": """
        SELECT COUNT(*) FROM stations_history
        WHERE num_bikes_available != num_mechanical + num_electrical
    """,
    "last_updated timestamps are plausible": """
        SELECT COUNT(*) FROM stations_history
        WHERE last_updated < TIMESTAMP '2026-01-01' OR last_updated > now() OR last_updated IS NULL
    """,
    "last_reported timestamps are plausible": """
        SELECT COUNT(*) FROM stations_history
        WHERE last_reported < TIMESTAMP '2026-01-01' OR last_reported > now() OR last_reported IS NULL
    """,
}