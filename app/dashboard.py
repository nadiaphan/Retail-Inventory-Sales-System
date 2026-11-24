from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import query_to_df


st.set_page_config(
    page_title="Retail Inventory & Sales System",
    layout="wide",
)


@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql, params=None):
    """Cache database query results for five minutes."""
    return query_to_df(sql, params)


@st.cache_data(ttl=300, show_spinner=False)
def get_filter_options():
    """Read all shared filter values from the database."""
    date_limits = run_query(
        """
        SELECT MIN(date) AS minimum_date, MAX(date) AS maximum_date
        FROM daily_inventory_sales;
        """
    )

    stores = run_query(
        """
        SELECT DISTINCT store_id
        FROM daily_inventory_sales
        ORDER BY store_id;
        """
    )["store_id"].tolist()

    regions = run_query(
        """
        SELECT DISTINCT region
        FROM daily_inventory_sales
        ORDER BY region;
        """
    )["region"].tolist()

    categories = run_query(
        """
        SELECT DISTINCT category
        FROM daily_inventory_sales
        ORDER BY category;
        """
    )["category"].tolist()

    products = run_query(
        """
        SELECT DISTINCT product_id
        FROM daily_inventory_sales
        ORDER BY product_id;
        """
    )["product_id"].tolist()

    return {
        "minimum_date": date_limits.loc[0, "minimum_date"],
        "maximum_date": date_limits.loc[0, "maximum_date"],
        "stores": stores,
        "regions": regions,
        "categories": categories,
        "products": products,
    }


def build_where_clause(start_date, end_date, stores, regions, categories, products):
    """Build fixed SQL filter clauses and a separate parameter list."""
    clauses = ["date BETWEEN %s AND %s"]
    params = [start_date, end_date]

    if stores:
        clauses.append("store_id = ANY(%s)")
        params.append(stores)

    if regions:
        clauses.append("region = ANY(%s)")
        params.append(regions)

    if categories:
        clauses.append("category = ANY(%s)")
        params.append(categories)

    if products:
        clauses.append("product_id = ANY(%s)")
        params.append(products)

    return " WHERE " + " AND ".join(clauses), params


def get_breakdown(dimension, where_clause, params):
    """Return units sold and revenue proxy for one approved dimension."""
    approved_dimensions = {
        "store_id": "store_id",
        "region": "region",
        "category": "category",
        "product_id": "product_id",
    }

    if dimension not in approved_dimensions:
        raise ValueError("Unsupported performance breakdown.")

    column_name = approved_dimensions[dimension]
    sql = f"""
        SELECT
            {column_name} AS breakdown,
            SUM(units_sold)::bigint AS total_units_sold,
            ROUND(
                SUM(units_sold * price * (1 - discount / 100.0)),
                2
            ) AS revenue_proxy
        FROM daily_inventory_sales
        {where_clause}
        GROUP BY {column_name}
        ORDER BY total_units_sold DESC, {column_name};
    """

    result = run_query(sql, params)

    if not result.empty:
        result["total_units_sold"] = pd.to_numeric(result["total_units_sold"])
        result["revenue_proxy"] = pd.to_numeric(result["revenue_proxy"])

    return result


def show_breakdown(title, dimension, where_clause, params):
    """Show one breakdown as native Streamlit charts and a table."""
    st.subheader(title)
    result = get_breakdown(dimension, where_clause, params)

    if result.empty:
        st.info("No data matches the selected filters.")
        return

    chart_data = result.set_index("breakdown")
    units_column, revenue_column = st.columns(2)

    with units_column:
        st.write("Total Units Sold")
        st.bar_chart(chart_data[["total_units_sold"]])

    with revenue_column:
        st.write("Revenue Proxy ($)")
        st.bar_chart(chart_data[["revenue_proxy"]])

    table = result.rename(
        columns={
            "breakdown": title.replace("By ", ""),
            "total_units_sold": "Total Units Sold",
            "revenue_proxy": "Revenue Proxy ($)",
        }
    )
    st.dataframe(table, hide_index=True, use_container_width=True)


def show_performance_page(where_clause, params, start_date, end_date):
    """Render Question 4: performance breakdowns."""
    st.title("Question 4: Performance Breakdowns")
    st.write(
        "Revenue proxy = Units Sold × Price × (1 − Discount / 100)."
    )

    count_sql = f"""
        SELECT COUNT(*) AS row_count
        FROM daily_inventory_sales
        {where_clause};
    """
    row_count = int(run_query(count_sql, params).loc[0, "row_count"])

    date_column, row_column = st.columns(2)
    date_column.metric(
        "Selected Date Range",
        f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}",
    )
    row_column.metric("Rows Included", f"{row_count:,}")

    show_breakdown("By Store", "store_id", where_clause, params)
    show_breakdown("By Region", "region", where_clause, params)
    show_breakdown("By Category", "category", where_clause, params)
    show_breakdown("By Product", "product_id", where_clause, params)


def show_placeholder(title, step_text):
    """Render a placeholder for a later dashboard question."""
    st.title(title)
    st.info(f"Coming in {step_text} — pattern follows Question 4.")


st.sidebar.title("Dashboard Navigation")
page = st.sidebar.radio(
    "Question",
    [
        "1. Inventory Health",
        "2. Sales vs. Forecast",
        "3. Replenishment Check",
        "4. Performance Breakdowns",
        "5. Driver Analysis",
    ],
    index=3,
)

try:
    filter_options = get_filter_options()
except Exception as error:
    st.error(f"Database connection failed: {error}")
    st.stop()

st.sidebar.header("Filters")
selected_dates = st.sidebar.date_input(
    "Date Range",
    value=(filter_options["minimum_date"], filter_options["maximum_date"]),
    min_value=filter_options["minimum_date"],
    max_value=filter_options["maximum_date"],
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

selected_stores = st.sidebar.multiselect("Store", filter_options["stores"])
selected_regions = st.sidebar.multiselect("Region", filter_options["regions"])
selected_categories = st.sidebar.multiselect(
    "Category", filter_options["categories"]
)
selected_products = st.sidebar.multiselect("Product", filter_options["products"])

where_clause, query_params = build_where_clause(
    start_date,
    end_date,
    selected_stores,
    selected_regions,
    selected_categories,
    selected_products,
)

if page == "1. Inventory Health":
    show_placeholder("Question 1: Inventory Health", "Step 5/6")
elif page == "2. Sales vs. Forecast":
    show_placeholder("Question 2: Sales vs. Forecast", "Step 5/6")
elif page == "3. Replenishment Check":
    show_placeholder("Question 3: Replenishment Check", "Step 7")
elif page == "4. Performance Breakdowns":
    show_performance_page(
        where_clause,
        query_params,
        start_date,
        end_date,
    )
else:
    show_placeholder("Question 5: Driver Analysis", "Step 7")
