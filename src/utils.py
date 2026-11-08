import os

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


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


def run_checks(con):
    failures = {}
    for name, sql in CHECKS.items():
        bad_rows = con.sql(sql).limit(1).fetchall()[0][0]
        if bad_rows:
            failures[name] = bad_rows
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")