# Sales Performance & KPI Analytics

An analytical **star schema** (`fact_sales` + `dim_customer` / `dim_product`
/ `dim_date`) with SQL KPI queries and an interactive dashboard, designed for
reporting on customer behavior, sales performance, and revenue trends.

## What it does
1. **Schema design** (`sql/star_schema_ddl.sql`) — a star schema: one fact
   table (`fact_sales`) with quantity/revenue/cost/margin, linked to three
   dimensions (customer, product, date)
2. **Integration** — `scripts/build_and_query.py` loads and cleans the raw
   customer/product/order/order-item CSVs, builds surrogate keys, and loads
   the star schema into a SQLite warehouse (`output/kpi_warehouse.db`)
3. **KPI queries** (`sql/kpi_queries.sql`) — 5 SQL views for BI reporting:
   - Monthly revenue/margin trend with MoM growth (CTE + `LAG` window fn)
   - Top products by revenue (`RANK()` window function)
   - Customer segment × region performance (AOV, revenue per customer)
   - Sales channel performance & margin %
   - Order status funnel (completed / cancelled / returned / pending)
4. **Dashboard** (`dashboard/index.html`) — a self-contained, offline HTML
   dashboard (Chart.js vendored locally, no external requests) visualizing
   all 5 KPI views

## Run it
```bash
pip install pandas
python3 scripts/build_and_query.py
```
Then open `dashboard/index.html` directly in a browser — it's fully static
and self-contained (KPI data is baked into the page at build time).

## Folder structure
```
data/raw/     -> source CSVs
sql/          -> star_schema_ddl.sql, kpi_queries.sql
scripts/      -> build_and_query.py
output/       -> kpi_warehouse.db + one CSV per KPI view
dashboard/    -> index.html, chart.umd.js, kpis.json, template.html
```

## Tech
Python (pandas), SQL (star schema, CTEs, window functions), SQLite, Chart.js.
