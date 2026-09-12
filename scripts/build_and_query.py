"""
Sales Performance & KPI Analytics
Builds the star schema (dim_customer, dim_product, dim_date, fact_sales),
loads it from the cleaned source data, runs the KPI queries, and exports
results as CSV + a single JSON file for the dashboard.

Run:  python3 scripts/build_and_query.py
"""
import json
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SQL = ROOT / "sql"
OUT = ROOT / "output"
DASH = ROOT / "dashboard"
DB_PATH = OUT / "kpi_warehouse.db"


def load_and_clean():
    customers = pd.read_csv(RAW / "raw_customers.csv").drop_duplicates(subset="customer_id")
    customers["region"] = customers["region"].str.strip().str.title()

    products = pd.read_csv(RAW / "raw_products.csv").drop_duplicates(subset="product_id")
    products["category"] = products["category"].str.strip().str.title()
    products["unit_cost"] = products["unit_cost"].abs()
    products["unit_price"] = products["unit_price"].abs()

    orders = pd.read_csv(RAW / "raw_orders.csv").drop_duplicates(subset="order_id")
    orders["order_date"] = pd.to_datetime(orders["order_date"], format="mixed", errors="coerce")
    orders = orders.dropna(subset=["order_date"])

    items = pd.read_csv(RAW / "raw_order_items.csv")
    items = items[(items["quantity"] > 0) & (items["unit_price"] > 0)]
    items = items[items["order_id"].isin(orders["order_id"]) & items["product_id"].isin(products["product_id"])]
    return customers, products, orders, items


def build_star_schema(conn, customers, products, orders, items):
    ddl = (SQL / "star_schema_ddl.sql").read_text()
    conn.executescript(ddl)

    # dim_customer
    dim_customer = customers[["customer_id", "customer_name", "region", "segment", "signup_date"]].copy()
    dim_customer.insert(0, "customer_key", range(1, len(dim_customer) + 1))
    dim_customer.to_sql("dim_customer", conn, if_exists="append", index=False)

    # dim_product
    dim_product = products[["product_id", "product_name", "category", "unit_cost", "unit_price"]].copy()
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))
    dim_product.to_sql("dim_product", conn, if_exists="append", index=False)

    # dim_date (from unique order dates in range)
    date_range = pd.date_range(orders["order_date"].min(), orders["order_date"].max(), freq="D")
    dim_date = pd.DataFrame({"full_date": date_range})
    dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.strftime("%B")
    dim_date["day_of_week"] = dim_date["full_date"].dt.strftime("%A")
    dim_date["is_weekend"] = dim_date["full_date"].dt.dayofweek.isin([5, 6])
    dim_date = dim_date[["date_key", "full_date", "year", "quarter", "month", "month_name",
                          "day_of_week", "is_weekend"]]
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)

    # fact_sales
    cust_map = dict(zip(dim_customer["customer_id"], dim_customer["customer_key"]))
    prod_map = dict(zip(dim_product["product_id"], dim_product["product_key"]))
    prod_cost = dict(zip(dim_product["product_id"], dim_product["unit_cost"]))

    orders_small = orders[["order_id", "customer_id", "order_date", "channel", "status"]].copy()
    fact = items.merge(orders_small, on="order_id", how="inner")
    fact["customer_key"] = fact["customer_id"].map(cust_map)
    fact["product_key"] = fact["product_id"].map(prod_map)
    fact["date_key"] = pd.to_datetime(fact["order_date"]).dt.strftime("%Y%m%d").astype(int)
    fact["revenue"] = fact["quantity"] * fact["unit_price"]
    fact["cost"] = fact["quantity"] * fact["product_id"].map(prod_cost)
    fact["margin"] = fact["revenue"] - fact["cost"]

    fact_final = fact[["order_id", "order_item_id", "customer_key", "product_key", "date_key",
                        "channel", "status", "quantity", "unit_price", "revenue", "cost", "margin"]]
    fact_final.to_sql("fact_sales", conn, if_exists="append", index=False)
    conn.commit()
    print(f"Loaded: dim_customer={len(dim_customer)}, dim_product={len(dim_product)}, "
          f"dim_date={len(dim_date)}, fact_sales={len(fact_final)}")


def run_kpis(conn):
    kpi_sql = (SQL / "kpi_queries.sql").read_text()
    conn.executescript(kpi_sql)
    conn.commit()

    views = ["kpi_monthly_trend", "kpi_top_products", "kpi_customer_segments",
             "kpi_channel_performance", "kpi_order_status_funnel"]
    results = {}
    for v in views:
        df = pd.read_sql(f"SELECT * FROM {v}", conn)
        df.to_csv(OUT / f"{v}.csv", index=False)
        results[v] = df
        print(f"  {v}: {len(df)} rows")
    return results


def export_dashboard_json(results):
    payload = {name: json.loads(df.to_json(orient="records")) for name, df in results.items()}
    (DASH / "kpis.json").write_text(json.dumps(payload, indent=2, default=str))
    print(f"Dashboard data written to {DASH / 'kpis.json'}")


def main():
    OUT.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)

    customers, products, orders, items = load_and_clean()
    print("STEP 1/3 — building star schema & loading facts/dims")
    build_star_schema(conn, customers, products, orders, items)

    print("STEP 2/3 — running KPI queries")
    results = run_kpis(conn)

    print("STEP 3/3 — exporting dashboard JSON")
    export_dashboard_json(results)

    conn.close()
    print(f"\nDone. Warehouse: {DB_PATH}\nOpen dashboard/index.html to view the KPI dashboard.")


if __name__ == "__main__":
    main()
