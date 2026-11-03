import os

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


CHECKS = {
    "id is unique": """
        SELECT COUNT(*) - COUNT(DISTINCT id) FROM result
    """,
    "no NULL keys": """
        SELECT COUNT(*) FROM result
        WHERE station_id IS NULL OR last_updated IS NULL
    """,
    "bike counts are non-negative": """
        SELECT COUNT(*) FROM result
        WHERE num_mechanical < 0 OR num_electrical < 0
    """,
    "mechanical + electrical = total": """
        SELECT COUNT(*) FROM result
        WHERE num_bikes_available != COALESCE(num_mechanical, 0) + COALESCE(num_electrical, 0)
    """,
    "bike types were parsed": """
        SELECT COUNT(*) FROM result
        WHERE num_mechanical IS NULL AND num_electrical IS NULL
    """,
    "every row matched a station": """
        SELECT COUNT(*) FROM result WHERE latitude IS NULL
    """,
    "timestamps are plausible": """
        SELECT COUNT(*) FROM result
        WHERE last_updated < TIMESTAMP '2020-01-01' OR last_updated > now()
    """,
}


def run_checks(con):
    failures = {}
    for name, sql in CHECKS.items():
        bad_rows = con.sql(sql).fetchone()[0]
        if bad_rows:
            failures[name] = bad_rows
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")