"""
Analisis cara 1 (pandas) dari data/online_retail_ii_clean.csv.
Menghasilkan findings.json + CSV agregat di data/:
  monthly_sales.csv, country_sales.csv, top_products.csv,
  hourly_sales.csv, weekday_sales.csv
Verifikasi independen (cara 2, SQL/SQLite) ada di scripts/verify_sqlite.py.
"""
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
NON_PRODUCT_PREFIX_NOTE = (
    "Ranking produk hanya StockCode yang diawali digit; kode berawalan huruf "
    "(POST, DOT, M, BANK CHARGES, AMAZONFEE, gift_*, dll) adalah ongkir/"
    "penyesuaian manual/voucher, bukan merchandise."
)

def main() -> None:
    df = pd.read_csv(DATA / "online_retail_ii_clean.csv", parse_dates=["invoice_date"],
                     dtype={"invoice": str, "stock_code": str})
    df["year_month"] = df["invoice_date"].dt.strftime("%Y-%m")
    df["hour"] = df["invoice_date"].dt.hour
    df["weekday"] = df["invoice_date"].dt.day_name()

    orders = df.groupby("invoice").agg(revenue=("revenue_gbp", "sum"),
                                       items=("quantity", "sum"))
    findings = {
        "dataset": "Online Retail II (UCI Machine Learning Repository)",
        "currency": "GBP",
        "revenue_definition": "Revenue = Quantity x Price untuk transaksi non-batal yang valid (lihat README, bagian Cleaning).",
        "date_range": {"start": str(df["invoice_date"].min()), "end": str(df["invoice_date"].max())},
        "total_revenue_gbp": round(float(df["revenue_gbp"].sum()), 2),
        "total_orders": int(df["invoice"].nunique()),
        "total_customers_identified": int(df["customer_id"].nunique()),
        "total_line_items": int(len(df)),
        "total_units_sold": int(df["quantity"].sum()),
        "average_order_value_gbp": round(float(orders["revenue"].mean()), 2),
        "median_order_value_gbp": round(float(orders["revenue"].median()), 2),
        "basket_size_items_per_order_mean": round(float(orders["items"].mean()), 2),
        "basket_size_items_per_order_median": float(orders["items"].median()),
        "orders_without_customer_id": int(orders.index.size - df.dropna(subset=["customer_id"])["invoice"].nunique()),
        "revenue_without_customer_id_gbp": round(float(df[df["customer_id"].isna()]["revenue_gbp"].sum()), 2),
        "uk_revenue_share_pct": round(100 * float(df[df["country"] == "United Kingdom"]["revenue_gbp"].sum() / df["revenue_gbp"].sum()), 2),
        "product_ranking_rule": NON_PRODUCT_PREFIX_NOTE,
    }

    # Temuan tambahan terverifikasi: konsentrasi order besar + repeat customer
    top_order = orders["revenue"].idxmax()
    big = orders[orders["revenue"] > 10000]
    findings["largest_single_order"] = {"invoice": str(top_order),
        "revenue_gbp": round(float(orders.loc[top_order, "revenue"]), 2),
        "items": int(orders.loc[top_order, "items"])}
    findings["orders_over_10000_gbp"] = {"orders": int(len(big)),
        "revenue_share_pct": round(100 * float(big["revenue"].sum() / df["revenue_gbp"].sum()), 2)}
    per_cust = df.dropna(subset=["customer_id"]).groupby("customer_id")["invoice"].nunique()
    findings["repeat_customers"] = {"customers_with_2plus_orders": int((per_cust > 1).sum()),
        "share_of_identified_customers_pct": round(100 * float((per_cust > 1).mean()), 2),
        "median_orders_per_customer": float(per_cust.median())}

    monthly = df.groupby("year_month").agg(revenue_gbp=("revenue_gbp", "sum"),
                                           orders=("invoice", "nunique"),
                                           units=("quantity", "sum")).reset_index()
    monthly["revenue_gbp"] = monthly["revenue_gbp"].round(2)
    monthly["aov_gbp"] = (monthly["revenue_gbp"] / monthly["orders"]).round(2)
    monthly.to_csv(DATA / "monthly_sales.csv", index=False)
    findings["best_month"] = monthly.loc[monthly["revenue_gbp"].idxmax()].to_dict()
    findings["monthly_sales"] = monthly.to_dict("records")

    country = (df.groupby("country").agg(revenue_gbp=("revenue_gbp", "sum"),
                                         orders=("invoice", "nunique"),
                                         customers=("customer_id", "nunique"),
                                         units=("quantity", "sum"))
               .reset_index().sort_values("revenue_gbp", ascending=False))
    country["revenue_gbp"] = country["revenue_gbp"].round(2)
    country.to_csv(DATA / "country_sales.csv", index=False)
    findings["top_countries_excl_uk"] = country[country["country"] != "United Kingdom"].head(5).to_dict("records")
    findings["countries_total"] = int(country.shape[0])

    prod = df[df["stock_code"].str.match(r"^\d")]
    desc_mode = (df.dropna(subset=["description"]).groupby("stock_code")["description"]
                 .agg(lambda s: s.mode().iat[0] if len(s.mode()) else None))
    top = (prod.groupby("stock_code").agg(revenue_gbp=("revenue_gbp", "sum"),
                                          units=("quantity", "sum"),
                                          orders=("invoice", "nunique"))
           .reset_index().sort_values("revenue_gbp", ascending=False).head(10))
    top["description"] = top["stock_code"].map(desc_mode)
    top["revenue_gbp"] = top["revenue_gbp"].round(2)
    top = top[["stock_code", "description", "revenue_gbp", "units", "orders"]]
    top.to_csv(DATA / "top_products.csv", index=False)
    findings["top10_products_by_revenue"] = top.to_dict("records")
    top_rev = float(top["revenue_gbp"].sum())
    findings["top10_revenue_share_pct"] = round(100 * top_rev / findings["total_revenue_gbp"], 2)

    hourly = df.groupby("hour").agg(revenue_gbp=("revenue_gbp", "sum"),
                                    orders=("invoice", "nunique")).reset_index()
    hourly["revenue_gbp"] = hourly["revenue_gbp"].round(2)
    hourly.to_csv(DATA / "hourly_sales.csv", index=False)
    findings["peak_hour"] = hourly.loc[hourly["orders"].idxmax()].to_dict()
    findings["hourly_sales"] = hourly.to_dict("records")

    order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = df.groupby("weekday").agg(revenue_gbp=("revenue_gbp", "sum"),
                                        orders=("invoice", "nunique")).reset_index()
    weekday["weekday"] = pd.Categorical(weekday["weekday"], order_days, ordered=True)
    weekday = weekday.sort_values("weekday")
    weekday["revenue_gbp"] = weekday["revenue_gbp"].round(2)
    weekday.to_csv(DATA / "weekday_sales.csv", index=False)
    findings["best_weekday_by_orders"] = weekday.loc[weekday["orders"].idxmax()].to_dict()
    findings["weekday_sales"] = weekday.assign(weekday=weekday["weekday"].astype(str)).to_dict("records")

    (BASE / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: findings[k] for k in ["total_revenue_gbp", "total_orders",
          "total_customers_identified", "average_order_value_gbp",
          "basket_size_items_per_order_mean", "date_range", "best_month",
          "peak_hour", "best_weekday_by_orders", "top10_revenue_share_pct"]}, indent=2, default=str))

if __name__ == "__main__":
    main()
