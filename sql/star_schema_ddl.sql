-- ============================================================================
-- Sales Performance & KPI Analytics — analytical star schema
-- Designed for reporting on customer behavior, sales performance, revenue
-- trends. Portable to PostgreSQL 15+ (SQLite demo variant built by
-- scripts/build_and_query.py uses the same table/column names).
-- ============================================================================

CREATE TABLE dim_customer (
    customer_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id    VARCHAR(10) UNIQUE NOT NULL,
    customer_name  TEXT,
    region         TEXT,
    segment        TEXT,
    signup_date    DATE
);

CREATE TABLE dim_product (
    product_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    VARCHAR(10) UNIQUE NOT NULL,
    product_name  TEXT,
    category      TEXT,
    unit_cost     NUMERIC(10,2),
    unit_price    NUMERIC(10,2)
);

CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,   -- YYYYMMDD
    full_date    DATE UNIQUE NOT NULL,
    year         INTEGER,
    quarter      INTEGER,
    month        INTEGER,
    month_name   TEXT,
    day_of_week  TEXT,
    is_weekend   BOOLEAN
);

CREATE TABLE fact_sales (
    sale_key      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      VARCHAR(10),
    order_item_id VARCHAR(12),
    customer_key  INTEGER REFERENCES dim_customer(customer_key),
    product_key   INTEGER REFERENCES dim_product(product_key),
    date_key      INTEGER REFERENCES dim_date(date_key),
    channel       TEXT,
    status        TEXT,
    quantity      INTEGER,
    unit_price    NUMERIC(10,2),
    revenue       NUMERIC(12,2),
    cost          NUMERIC(12,2),
    margin        NUMERIC(12,2)
);

CREATE INDEX idx_fact_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_product  ON fact_sales(product_key);
CREATE INDEX idx_fact_date     ON fact_sales(date_key);
