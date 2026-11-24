import os
from pathlib import Path

import pandas as pd
import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parent


def _load_env_file(env_path):
    """Load values from .env without replacing existing environment variables."""
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"').strip("'")

            if name:
                os.environ.setdefault(name, value)


def get_connection():
    """Return a PostgreSQL connection using environment variables."""
    _load_env_file(PROJECT_ROOT / ".env")

    variable_names = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    missing = [name for name in variable_names if not os.environ.get(name)]

    if missing:
        raise ValueError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def query_to_df(sql, params=None):
    """Run a parameterized SELECT query and return a pandas DataFrame."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])
            rows = cursor.fetchall()
            column_names = [column.name for column in cursor.description]
    finally:
        connection.close()

    return pd.DataFrame(rows, columns=column_names)
