import os
from velotoulouse.const import CHECKS

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value



def run_checks(con):
    failures = {}
    for name, sql in CHECKS.items():
        bad_rows = con.sql(sql).limit(1).fetchall()[0][0]
        if bad_rows:
            failures[name] = bad_rows
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")