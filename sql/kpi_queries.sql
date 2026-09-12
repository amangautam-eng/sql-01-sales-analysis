-- ============================================================================
-- KPI reporting queries against the star schema (fact_sales + dims)
-- ============================================================================

-- 1) REVENUE & MARGIN TREND BY MONTH, with MoM growth (CTE + window function)
CREATE VIEW kpi_monthly_trend AS
WITH monthly AS (
    SELECT
        d.year, d.month, d.month_name,
        SUM(f.revenue) AS revenue,
        SUM(f.margin)  AS margin,
        COUNT(DISTINCT f.order_id) AS orders
    FROM fact_sales f
    JOIN dim_date d ON d.date_key = f.date_key
    WHERE f.status = 'Completed'
    GROUP BY d.year, d.month, d.month_name
)
SELECT *,
    ROUND(revenue * 1.0 / orders, 2) AS avg_order_value,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY year, month)) * 100.0
        / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0), 2
    ) AS revenue_mom_growth_pct
FROM monthly
ORDER BY year, month;

-- 2) TOP PRODUCTS BY REVENUE (window function RANK, category share)
CREATE VIEW kpi_top_products AS
SELECT
    p.product_name, p.category,
    SUM(f.revenue) AS revenue,
    SUM(f.quantity) AS units_sold,
    SUM(f.margin) AS margin,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
WHERE f.status = 'Completed'
GROUP BY p.product_name, p.category;

-- 3) CUSTOMER SEGMENTATION KPIs — revenue & AOV by segment/region
CREATE VIEW kpi_customer_segments AS
SELECT
    c.segment, c.region,
    COUNT(DISTINCT c.customer_key) AS customers,
    COUNT(DISTINCT f.order_id) AS orders,
    SUM(f.revenue) AS revenue,
    ROUND(SUM(f.revenue) * 1.0 / COUNT(DISTINCT f.order_id), 2) AS avg_order_value,
    ROUND(SUM(f.revenue) * 1.0 / COUNT(DISTINCT c.customer_key), 2) AS revenue_per_customer
FROM fact_sales f
JOIN dim_customer c ON c.customer_key = f.customer_key
WHERE f.status = 'Completed'
GROUP BY c.segment, c.region;

-- 4) SALES CHANNEL PERFORMANCE
CREATE VIEW kpi_channel_performance AS
SELECT
    channel,
    COUNT(DISTINCT order_id) AS orders,
    SUM(revenue) AS revenue,
    ROUND(SUM(revenue) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    ROUND(SUM(margin) * 100.0 / NULLIF(SUM(revenue), 0), 2) AS margin_pct
FROM fact_sales
WHERE status = 'Completed'
GROUP BY channel;

-- 5) ORDER STATUS FUNNEL (cancellation / return rate KPI)
CREATE VIEW kpi_order_status_funnel AS
SELECT
    status,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(COUNT(DISTINCT order_id) * 100.0 / SUM(COUNT(DISTINCT order_id)) OVER (), 2) AS pct_of_total
FROM fact_sales
GROUP BY status;
