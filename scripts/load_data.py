import csv
import os
import sys
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DEFAULT_CSV_PATH = PROJECT_ROOT / "retail_store_inventory_cleaned.csv"
BATCH_SIZE = 1000

CSV_COLUMNS = [
    "date",
    "store_id",
    "product_id",
    "category",
    "region",
    "inventory_level",
    "units_sold",
    "units_ordered",
    "demand_forecast",
    "price",
    "discount",
    "weather_condition",
    "holiday_promotion",
    "competitor_pricing",
    "seasonality",
]


def load_env_file(env_path):
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


def get_database_settings():
    """Read the required database connection settings."""
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

    return {
        "host": os.environ["DB_HOST"],
        "port": os.environ["DB_PORT"],
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def get_csv_path():
    """Use a command-line path, CSV_PATH, or the default repository CSV."""
    if len(sys.argv) > 2:
        raise ValueError("Usage: python scripts/load_data.py [csv_path]")

    if len(sys.argv) == 2:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path(os.environ.get("CSV_PATH", DEFAULT_CSV_PATH))

    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    return csv_path


def recreate_tables(cursor):
    """Drop existing tables and recreate them from sql/schema.sql."""
    drop_sql = """
        DROP TABLE IF EXISTS daily_inventory_sales;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS stores;
        DROP TABLE IF EXISTS raw_retail_data;
    """

    cursor.execute(drop_sql)

    with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
        cursor.execute(schema_file.read())


def load_staging_table(cursor, csv_path):
    """Load the CSV into raw_retail_data in batches."""
    placeholders = ", ".join(["%s"] * len(CSV_COLUMNS))
    column_names = ", ".join(CSV_COLUMNS)
    insert_sql = (
        f"INSERT INTO raw_retail_data ({column_names}) "
        f"VALUES ({placeholders})"
    )

    row_count = 0
    batch = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames != CSV_COLUMNS:
            raise ValueError(
                "CSV columns do not match raw_retail_data. "
                f"Expected {CSV_COLUMNS}, but found {reader.fieldnames}."
            )

        for row in reader:
            batch.append(tuple(row[column] for column in CSV_COLUMNS))
            row_count += 1

            if len(batch) == BATCH_SIZE:
                cursor.executemany(insert_sql, batch)
                batch = []

        if batch:
            cursor.executemany(insert_sql, batch)

    return row_count


def populate_clean_tables(cursor):
    """Convert the staging data into the normalized tables."""
    cursor.execute(
        """
        INSERT INTO stores (store_id)
        SELECT DISTINCT store_id
        FROM raw_retail_data;
        """
    )

    cursor.execute(
        """
        INSERT INTO products (product_id)
        SELECT DISTINCT product_id
        FROM raw_retail_data;
        """
    )

    cursor.execute(
        """
        INSERT INTO daily_inventory_sales (
            date,
            store_id,
            product_id,
            category,
            region,
            inventory_level,
            units_sold,
            units_ordered,
            demand_forecast,
            price,
            discount,
            weather_condition,
            holiday_promotion,
            competitor_pricing,
            seasonality
        )
        SELECT
            date::date,
            store_id,
            product_id,
            category,
            region,
            inventory_level::integer,
            units_sold::integer,
            units_ordered::integer,
            demand_forecast::numeric,
            price::numeric,
            discount::integer,
            weather_condition,
            holiday_promotion::integer,
            competitor_pricing::numeric,
            seasonality
        FROM raw_retail_data;
        """
    )


def get_load_report(cursor):
    """Return table counts and the date range."""
    counts = {}

    for table_name in [
        "raw_retail_data",
        "daily_inventory_sales",
        "stores",
        "products",
    ]:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        counts[table_name] = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(date), MAX(date) FROM daily_inventory_sales;")
    minimum_date, maximum_date = cursor.fetchone()

    return counts, minimum_date, maximum_date


def print_load_report(csv_row_count, counts, minimum_date, maximum_date):
    """Print the final results."""
    print("Load complete")
    print(f"CSV data rows: {csv_row_count}")
    print(f"raw_retail_data rows: {counts['raw_retail_data']}")
    print(f"daily_inventory_sales rows: {counts['daily_inventory_sales']}")
    print(f"stores rows: {counts['stores']}")
    print(f"products rows: {counts['products']}")
    print(f"Minimum date: {minimum_date}")
    print(f"Maximum date: {maximum_date}")


def main():
    load_env_file(PROJECT_ROOT / ".env")
    database_settings = get_database_settings()
    csv_path = get_csv_path()

    with psycopg2.connect(**database_settings) as connection:
        with connection.cursor() as cursor:
            recreate_tables(cursor)
            csv_row_count = load_staging_table(cursor, csv_path)
            populate_clean_tables(cursor)
            counts, minimum_date, maximum_date = get_load_report(cursor)

            if counts["raw_retail_data"] != csv_row_count:
                raise ValueError("Staging row count does not match the CSV row count.")

            if counts["daily_inventory_sales"] != csv_row_count:
                raise ValueError("Fact table row count does not match the CSV row count.")

    print_load_report(csv_row_count, counts, minimum_date, maximum_date)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Load failed: {error}", file=sys.stderr)
        sys.exit(1)
