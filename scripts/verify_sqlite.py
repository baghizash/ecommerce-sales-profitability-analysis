"""
Verifikasi cara 2 (independen): hitung ulang angka kunci dari clean CSV
memakai SQL murni lewat SQLite in-memory, lalu cocokkan dengan findings.json
yang dibuat scripts/analyze.py (pandas). Exit code 1 kalau ada yang tidak cocok.
Database dibuat in-memory - tidak ada file .db yang ditulis ke repo.
"""
import json, sqlite3, sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
TOL = 0.02  # toleransi pembulatan GBP

def main() -> None:
    findings = json.loads((BASE / "findings.json").read_text(encoding="utf-8"))
    df = pd.read_csv(BASE / "data" / "online_retail_ii_clean.csv",
                     dtype={"invoice": str, "stock_code": str})
    con = sqlite3.connect(":memory:")
    df.to_sql("sales_clean", con, index=False)
    q = lambda sql: con.execute(sql).fetchone()

    checks = []
    def check(name, sql_value, expected):
        ok = abs(float(sql_value) - float(expected)) <= TOL if isinstance(expected, (int, float)) else str(sql_value) == str(expected)
        checks.append((name, sql_value, expected, ok))

    check("total_revenue_gbp", q("SELECT ROUND(SUM(revenue_gbp),2) FROM sales_clean")[0], findings["total_revenue_gbp"])
    check("total_orders", q("SELECT COUNT(DISTINCT invoice) FROM sales_clean")[0], findings["total_orders"])
    check("total_customers_identified", q("SELECT COUNT(DISTINCT customer_id) FROM sales_clean WHERE customer_id IS NOT NULL")[0], findings["total_customers_identified"])
    check("total_units_sold", q("SELECT SUM(quantity) FROM sales_clean")[0], findings["total_units_sold"])
    check("average_order_value_gbp", q("SELECT ROUND(SUM(rev)/COUNT(*),2) FROM (SELECT SUM(revenue_gbp) rev FROM sales_clean GROUP BY invoice)")[0], findings["average_order_value_gbp"])
    check("basket_size_mean", q("SELECT ROUND(AVG(items),2) FROM (SELECT SUM(quantity) items FROM sales_clean GROUP BY invoice)")[0], findings["basket_size_items_per_order_mean"])
    check("date_start", q("SELECT MIN(invoice_date) FROM sales_clean")[0], findings["date_range"]["start"])
    check("date_end", q("SELECT MAX(invoice_date) FROM sales_clean")[0], findings["date_range"]["end"])
    check("best_month_revenue", q("SELECT ROUND(SUM(revenue_gbp),2) FROM sales_clean WHERE substr(invoice_date,1,7)=(SELECT substr(invoice_date,1,7) FROM sales_clean GROUP BY 1 ORDER BY SUM(revenue_gbp) DESC LIMIT 1)")[0], findings["best_month"]["revenue_gbp"])
    top_sql = con.execute("""SELECT stock_code, ROUND(SUM(revenue_gbp),2) FROM sales_clean
        WHERE stock_code GLOB '[0-9]*' GROUP BY stock_code ORDER BY 2 DESC LIMIT 10""").fetchall()
    top_pd = [(r["stock_code"], r["revenue_gbp"]) for r in findings["top10_products_by_revenue"]]
    check("top10_products_match", int(top_sql == [(c, v) for c, v in top_pd]), 1)
    top_country_sql = con.execute("""SELECT country FROM sales_clean WHERE country<>'United Kingdom'
        GROUP BY country ORDER BY SUM(revenue_gbp) DESC LIMIT 1""").fetchone()[0]
    check("top_country_excl_uk", top_country_sql, findings["top_countries_excl_uk"][0]["country"])
    peak_hour_sql = q("SELECT CAST(substr(invoice_date,12,2) AS INTEGER) FROM sales_clean GROUP BY 1 ORDER BY COUNT(DISTINCT invoice) DESC LIMIT 1")[0]
    check("peak_hour", peak_hour_sql, findings["peak_hour"]["hour"])

    failed = [c for c in checks if not c[3]]
    for name, got, exp, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: sql={got}  pandas/findings={exp}")
    print(f"\n{len(checks)-len(failed)}/{len(checks)} cocok")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
