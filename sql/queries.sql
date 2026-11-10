-- =====================================================================
-- E-Commerce Sales Performance & Profitability - Online Retail II (UCI)
-- 12 query SQL terhadap tabel sales_clean.
-- Cara jalan: python scripts/load_to_sqlite.py /tmp/ecommerce_sales.db
--             sqlite3 /tmp/ecommerce_sales.db < sql/queries.sql
-- Definisi: revenue_gbp = quantity x price_gbp (transaksi non-batal valid).
-- Catatan profitability: dataset tidak punya kolom cost, jadi tidak ada
-- query profit margin - yang diukur adalah kualitas revenue (AOV, basket
-- size, konsentrasi produk/negara, revenue per customer).
-- =====================================================================

-- Q1. KPI ringkasan: total revenue, order, customer teridentifikasi, AOV, basket size
SELECT ROUND(SUM(revenue_gbp), 2)                                   AS total_revenue_gbp,
       COUNT(DISTINCT invoice)                                       AS total_orders,
       COUNT(DISTINCT customer_id)                                   AS customers_identified,
       ROUND(SUM(revenue_gbp) / COUNT(DISTINCT invoice), 2)          AS aov_gbp,
       ROUND(1.0 * SUM(quantity) / COUNT(DISTINCT invoice), 2)       AS basket_size_items_per_order
FROM sales_clean;

-- Q2. Tren bulanan: revenue, order, unit, AOV per bulan
SELECT substr(invoice_date, 1, 7)                            AS year_month,
       ROUND(SUM(revenue_gbp), 2)                            AS revenue_gbp,
       COUNT(DISTINCT invoice)                               AS orders,
       SUM(quantity)                                         AS units,
       ROUND(SUM(revenue_gbp) / COUNT(DISTINCT invoice), 2)  AS aov_gbp
FROM sales_clean
GROUP BY year_month
ORDER BY year_month;

-- Q3. Top 10 produk (merchandise saja) by revenue
-- StockCode berawalan huruf (POST, DOT, M, BANK CHARGES, gift_*) dikeluarkan:
-- itu ongkir / penyesuaian manual / voucher, bukan produk.
SELECT stock_code,
       MAX(description)                  AS description,
       ROUND(SUM(revenue_gbp), 2)        AS revenue_gbp,
       SUM(quantity)                     AS units,
       COUNT(DISTINCT invoice)           AS orders
FROM sales_clean
WHERE stock_code GLOB '[0-9]*'
GROUP BY stock_code
ORDER BY revenue_gbp DESC
LIMIT 10;

-- Q4. Revenue per negara (semua negara, urut revenue)
SELECT country,
       ROUND(SUM(revenue_gbp), 2)                            AS revenue_gbp,
       ROUND(100.0 * SUM(revenue_gbp) / (SELECT SUM(revenue_gbp) FROM sales_clean), 2) AS revenue_share_pct,
       COUNT(DISTINCT invoice)                               AS orders,
       COUNT(DISTINCT customer_id)                           AS customers
FROM sales_clean
GROUP BY country
ORDER BY revenue_gbp DESC;

-- Q5. Top 10 negara di luar United Kingdom
SELECT country, ROUND(SUM(revenue_gbp), 2) AS revenue_gbp, COUNT(DISTINCT invoice) AS orders
FROM sales_clean
WHERE country <> 'United Kingdom'
GROUP BY country
ORDER BY revenue_gbp DESC
LIMIT 10;

-- Q6. Pola jam: order dan revenue per jam buka transaksi
SELECT CAST(substr(invoice_date, 12, 2) AS INTEGER) AS hour,
       COUNT(DISTINCT invoice)                      AS orders,
       ROUND(SUM(revenue_gbp), 2)                   AS revenue_gbp
FROM sales_clean
GROUP BY hour
ORDER BY hour;

-- Q7. Pola hari dalam seminggu (0 = Minggu di SQLite strftime %w)
SELECT strftime('%w', invoice_date)       AS weekday_num,
       COUNT(DISTINCT invoice)            AS orders,
       ROUND(SUM(revenue_gbp), 2)         AS revenue_gbp
FROM sales_clean
GROUP BY weekday_num
ORDER BY weekday_num;

-- Q8. Distribusi nilai order: order kecil vs besar
SELECT CASE WHEN rev < 10 THEN '01. <10'
            WHEN rev < 25 THEN '02. 10-24.99'
            WHEN rev < 50 THEN '03. 25-49.99'
            WHEN rev < 100 THEN '04. 50-99.99'
            ELSE '05. >=100' END                       AS order_value_band,
       COUNT(*)                                        AS orders,
       ROUND(SUM(rev), 2)                              AS revenue_gbp
FROM (SELECT invoice, SUM(revenue_gbp) AS rev FROM sales_clean GROUP BY invoice)
GROUP BY order_value_band
ORDER BY order_value_band;

-- Q9. Top 20 customer teridentifikasi by revenue (wholesale terlihat di sini)
SELECT customer_id,
       COUNT(DISTINCT invoice)             AS orders,
       SUM(quantity)                       AS units,
       ROUND(SUM(revenue_gbp), 2)          AS revenue_gbp,
       ROUND(SUM(revenue_gbp) / COUNT(DISTINCT invoice), 2) AS aov_gbp,
       MIN(substr(invoice_date, 1, 10))    AS first_order_date,
       MAX(substr(invoice_date, 1, 10))    AS last_order_date
FROM sales_clean
WHERE customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY revenue_gbp DESC
LIMIT 20;

-- Q10. Repeat purchase: berapa customer yang order lebih dari sekali
SELECT CASE WHEN n_orders = 1 THEN '1 order' ELSE 'repeat (2+ order)' END AS segment,
       COUNT(*) AS customers
FROM (SELECT customer_id, COUNT(DISTINCT invoice) AS n_orders
      FROM sales_clean WHERE customer_id IS NOT NULL GROUP BY customer_id)
GROUP BY segment;

-- Q11. Revenue tanpa Customer ID (baris valid yang tidak bisa diatribusikan ke customer)
SELECT ROUND(SUM(revenue_gbp), 2) AS revenue_without_customer_id_gbp,
       COUNT(DISTINCT invoice)    AS orders_without_customer_id,
       ROUND(100.0 * SUM(revenue_gbp) / (SELECT SUM(revenue_gbp) FROM sales_clean), 2) AS share_pct
FROM sales_clean
WHERE customer_id IS NULL;

-- Q12. Produk dengan unit terjual terbanyak (volume, bukan revenue)
SELECT stock_code, MAX(description) AS description,
       SUM(quantity) AS units, ROUND(SUM(revenue_gbp), 2) AS revenue_gbp
FROM sales_clean
WHERE stock_code GLOB '[0-9]*'
GROUP BY stock_code
ORDER BY units DESC
LIMIT 10;
