# Data Dictionary - Retail Store Inventory Dataset

**Team notes for the DB project**

Dataset is from Kaggle: [Retail Store Inventory Forecasting Dataset](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset) (by anirudhchauhan)

Basically each row = one product, at one store, on one day. So I'm going to use this list of columns to figure out our tables. The ID-type stuff (store, product) should be their own tables and the daily numbers go in one big fact table.

## Columns

| Column | Type | What it is | Notes |
|---|---|---|---|
| Date | DATE | the day of the observation | one row per day, so this is part of the key |
| Store ID | TEXT | store code | like S001. goes in **stores** table |
| Product ID | TEXT | product code | like P0001. goes in **products** table |
| Category | TEXT | what category the product is in | belongs to products, good for grouping (Toys, Groceries, etc) |
| Region | TEXT | where the store is | North / South / East / West. belongs to stores |
| Inventory Level | INTEGER | how many units are in stock at the store that day | use this to find low stock |
| Units Sold | INTEGER | units sold that day | main sales number |
| Units Ordered | INTEGER | units reordered that day | compare to Units Sold / forecast to see restocking |
| Demand Forecast | NUMERIC | predicted demand for that product/store/day | compare to actual Units Sold to check how accurate the forecast is |
| Price | NUMERIC ($) | price per unit | this is BEFORE the discount |
| Discount | INTEGER (%) | discount % that day | see if discounts actually increase sales |
| Weather Condition | TEXT | weather that day | Sunny / Rainy / Snowy / Cloudy |
| Holiday/Promotion | INTEGER (0/1) | 1 = holiday or promo that day, 0 = not | for seeing if promos help sales |
| Competitor Pricing | NUMERIC ($) | what competitors charge for a similar product | compare with our Price |
| Seasonality | TEXT | season of that date | Spring / Summer / Autumn / Winter, comes from Date |

## Schema ideas (still a draft!!)

- **stores**: Store ID (PK), Region
- **products**: Product ID (PK), Category
- **daily_inventory_sales**: Date + Store ID + Product ID together as the composite key, then everything else (Inventory Level, Units Sold, Units Ordered, Demand Forecast, Price, Discount, Weather Condition, Holiday/Promotion, Competitor Pricing, Seasonality)

Side note: Seasonality can be figured out from Date, so technically it's redundant. I think we keep it in the fact table anyway so queries are easier, or we could make a view for it instead. Need to ask the group which way we want to go.

**TODO:**
- double check that every Product ID only has ONE category (otherwise products table breaks)
- same for Store ID and Region
- decide on seasonality (keep or view)
