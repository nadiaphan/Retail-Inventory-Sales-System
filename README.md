# Retail Inventory & Sales Management System

## Project Overview
This project will develop a retail inventory and sales management system that helps retail managers monitor sales, inventory levels, product demand, and replenishment activity across multiple stores.

## Data Source
### Retail Store Inventory Forecasting Dataset

**Source:** Kaggle  
**Dataset Link:** https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset?

This dataset contains retail sales and inventory information across multiple stores and products. The data includes:

- Date
- Store ID
- Product ID
- Product Category
- Region
- Inventory Level
- Units Sold
- Units Ordered
- Demand Forecast
- Price
- Discount
- Weather Condition
- Holiday/Promotion
- Competitor Pricing
- Seasonality

## System Components
- SQL relational database
- Docker containerization
- Interactive dashboard
- Retail sales and inventory analysis

## Expected Capabilities
- Monitor inventory levels
- Identify low-stock products
- Analyze units sold and units ordered
- Compare sales with demand forecasts
- Analyze performance by store, product, category, and region
- Examine the effects of discounts, promotions, and seasonality

## Repository Guide

- `docs/`: Project documentation, including the dataset data dictionary.
- `sql/`: SQL files for the normalized database schema.
- `.env.example`: Example environment configuration.
- `Dockerfile` and `docker-compose.yml`: Docker configuration files.
- `retail_inventory_setup.ipynb`: Retail inventory setup notebook.
- `retail_store_inventory_cleaned.csv`: Cleaned retail inventory dataset.

## Setup and data loading

Run these commands from the repository root.

1. Copy `.env.example` to `.env` and replace the example password with a real local password. Keep `.env` out of GitHub.

   ```powershell
   Copy-Item .env.example .env
   ```

2. Set `DB_HOST=localhost` in `.env`, then start the PostgreSQL database.

   ```powershell
   docker compose up -d db
   ```

3. Install the PostgreSQL driver on the local machine.

   ```powershell
   pip install psycopg2-binary
   ```

4. Load the dataset.

   ```powershell
   python scripts/load_data.py
   ```

   To load a different CSV, pass its path as an argument or set the optional `CSV_PATH` environment variable.

5. A successful load of the current dataset prints:

   ```text
   Load complete
   CSV data rows: 73100
   raw_retail_data rows: 73100
   daily_inventory_sales rows: 73100
   stores rows: 5
   products rows: 20
   Minimum date: 2022-01-01
   Maximum date: 2024-01-01
   ```

## Running the dashboard

Run these commands from the repository root.

1. Start the PostgreSQL database. The data must already be loaded with `python scripts/load_data.py`; otherwise, the dashboard will have no data to display.

   ```powershell
   docker compose up -d db
   ```

2. Install the dashboard packages for Python 3.12.

   ```powershell
   python -m pip install streamlit pandas psycopg2-binary
   ```

3. Set `DB_HOST=localhost` in `.env`, then start the dashboard.

   ```powershell
   python -m streamlit run app/dashboard.py
   ```

A working dashboard shows the five-question navigation and shared filters in the left sidebar. The Question 4 page shows performance breakdowns by store, region, category, and product, with charts and tables for total units sold and the revenue proxy.
