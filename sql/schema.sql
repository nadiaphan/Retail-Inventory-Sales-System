-- Raw CSV data goes here first.
-- No primary key because duplicate rows from the CSV should be kept.
CREATE TABLE raw_retail_data (
    date TEXT,
    store_id TEXT,
    product_id TEXT,
    category TEXT,
    region TEXT,
    inventory_level TEXT,
    units_sold TEXT,
    units_ordered TEXT,
    demand_forecast TEXT,
    price TEXT,
    discount TEXT,
    weather_condition TEXT,
    holiday_promotion TEXT,
    competitor_pricing TEXT,
    seasonality TEXT
);

-- Store information
CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,
    region TEXT
);

-- Product information
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    category TEXT
);

-- Daily inventory and sales data
CREATE TABLE daily_inventory_sales (
    date DATE,
    store_id TEXT,
    product_id TEXT,
    inventory_level INTEGER,
    units_sold INTEGER,
    units_ordered INTEGER,
    demand_forecast NUMERIC,
    price NUMERIC,
    discount INTEGER,
    weather_condition TEXT,
    holiday_promotion INTEGER,
    competitor_pricing NUMERIC,
    seasonality TEXT,
    PRIMARY KEY (date, store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);
