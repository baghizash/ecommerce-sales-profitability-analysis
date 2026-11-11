#!/usr/bin/env python3
"""Buat 12 chart Tahap 2 + customer_repeat_summary.csv dari data bersih Online Retail II.

Definisi sama persis dengan Tahap 1 (findings.json):
- Revenue = Quantity x Price (kolom revenue_gbp di data bersih = hasil kali itu,
  hanya transaksi valid non-batal; aturan cleaning ada di scripts/clean_data.py Tahap 1).
- Ranking produk hanya StockCode berawalan digit.
- Repeat customer = customer teridentifikasi dengan 2 order atau lebih.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent  # staging root (atau repo root setelah disalin)
CHART_DIR = ROOT / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

DATA_CANDIDATES = [
    ROOT / "data" / "online_retail_ii_clean.csv",
    Path.home() / "workspace" / "ecommerce-sales-profitability" / "data" / "online_retail_ii_clean.csv",
]
FINDINGS_CANDIDATES = [
    ROOT / "findings.json",
    Path.home() / "workspace" / "ecommerce-sales-profitability" / "findings.json",
]

MARINE = "#1B4F72"
TEAL = "#2E86AB"
TANGERINE = "#F18F01"
GREEN = "#3E8914"
PLUM = "#6C3483"
GREY = "#7F8C8D"
LIGHT = "#AED6F1"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.25,
})


def fmt_gbp(x):
    return f"£{x:,.0f}"


def load_data():
    for p in DATA_CANDIDATES:
        if p.exists():
            df = pd.read_csv(p, dtype={"stock_code": str, "invoice": str})
            break
    else:
        raise FileNotFoundError("online_retail_ii_clean.csv tidak ditemukan di kandidat path mana pun")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["revenue_gbp"] = df["quantity"] * df["price_gbp"]  # definisi Tahap 1, dihitung ulang dari kolom dasar
    return df


def main():
    df = load_data()
    orders = df.groupby("invoice").agg(
        order_revenue=("revenue_gbp", "sum"),
        order_items=("quantity", "sum"),
        customer_id=("customer_id", "first"),
    ).reset_index()
    monthly = df.set_index("invoice_date").resample("ME").agg(
        revenue=("revenue_gbp", "sum"), orders=("invoice", "nunique")
    ).reset_index()
    monthly["year_month"] = monthly["invoice_date"].dt.strftime("%Y-%m")
    monthly["aov"] = monthly["revenue"] / monthly["orders"]

    # ---------- 01 trend revenue bulanan ----------
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(monthly["year_month"], monthly["revenue"], marker="o", color=MARINE, linewidth=2)
    ax.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.12, color=TEAL)
    best = monthly.loc[monthly["revenue"].idxmax()]
    ax.annotate(f"Puncak: {best['year_month']}\n{fmt_gbp(best['revenue'])}",
                xy=(list(monthly["year_month"]).index(best["year_month"]), best["revenue"]),
                xytext=(-90, 18), textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color=TANGERINE), color=TANGERINE, fontweight="bold")
    ax.set_title("Trend Revenue Bulanan (Des 2009 - Des 2011, parsial)")
    ax.set_ylabel("Revenue (GBP)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout(); fig.savefig(CHART_DIR / "01_monthly_revenue_trend.png"); plt.close(fig)

    # ---------- 02 musiman: revenue per bulan kalender, per tahun ----------
    seas = df.copy()
    seas["year"] = seas["invoice_date"].dt.year
    seas["month"] = seas["invoice_date"].dt.month
    seas_g = seas.groupby(["month", "year"])["revenue_gbp"].sum().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    for yr, color in [(2010, TEAL), (2011, TANGERINE)]:
        if yr in seas_g.columns:
            ax.plot(seas_g.index, seas_g[yr], marker="o", label=str(yr), color=color, linewidth=2)
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(month_names)
    ax.set_title("Pola Musiman: Revenue per Bulan Kalender, 2010 vs 2011")
    ax.set_ylabel("Revenue (GBP)"); ax.legend(title="Tahun")
    fig.tight_layout(); fig.savefig(CHART_DIR / "02_seasonal_revenue_by_month_year.png"); plt.close(fig)

    # ---------- 03 top 10 produk ----------
    prod = df[df["stock_code"].str.match(r"^\d", na=False)].copy()
    desc_map = prod.groupby("stock_code")["description"].agg(lambda s: s.mode().iat[0] if len(s.mode()) else "")
    top10 = prod.groupby("stock_code").agg(revenue=("revenue_gbp", "sum"), units=("quantity", "sum")).nlargest(10, "revenue").iloc[::-1]
    labels = [f"{desc_map.get(i, i)}"[:42] for i in top10.index]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.barh(labels, top10["revenue"], color=MARINE)
    for i, v in enumerate(top10["revenue"]):
        ax.text(v * 1.01, i, fmt_gbp(v), va="center", fontsize=9)
    ax.set_xlim(0, top10["revenue"].max() * 1.18)
    ax.set_title("Top 10 Produk by Revenue (hanya StockCode berawalan digit)")
    ax.set_xlabel("Revenue (GBP)")
    fig.tight_layout(); fig.savefig(CHART_DIR / "03_top10_products.png"); plt.close(fig)

    # ---------- 04 top negara non-UK ----------
    ctry = df.groupby("country").agg(revenue=("revenue_gbp", "sum"), orders=("invoice", "nunique"))
    top_ctry = ctry[ctry.index != "United Kingdom"].nlargest(8, "revenue").iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.barh(top_ctry.index, top_ctry["revenue"], color=TEAL)
    for i, v in enumerate(top_ctry["revenue"]):
        ax.text(v * 1.01, i, fmt_gbp(v), va="center", fontsize=9)
    ax.set_xlim(0, top_ctry["revenue"].max() * 1.2)
    ax.set_title("Top 8 Negara di Luar United Kingdom by Revenue")
    ax.set_xlabel("Revenue (GBP)")
    fig.tight_layout(); fig.savefig(CHART_DIR / "04_top_countries_non_uk.png"); plt.close(fig)

    # ---------- 05 pola jam ----------
    df["hour"] = df["invoice_date"].dt.hour
    hourly = df.groupby("hour").agg(revenue=("revenue_gbp", "sum"), orders=("invoice", "nunique")).reindex(range(6, 21), fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.bar(hourly.index.astype(str), hourly["orders"], color=TEAL)
    ax.set_title("Pola Order per Jam (puncak pukul 12.00)")
    ax.set_xlabel("Jam"); ax.set_ylabel("Jumlah order")
    fig.tight_layout(); fig.savefig(CHART_DIR / "05_hourly_pattern.png"); plt.close(fig)

    # ---------- 06 pola hari ----------
    df["weekday"] = df["invoice_date"].dt.day_name()
    order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    id_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    wd = df.groupby("weekday").agg(revenue=("revenue_gbp", "sum"), orders=("invoice", "nunique")).reindex(order_days)
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    bars = ax.bar(id_days, wd["orders"], color=[TANGERINE if d == "Thursday" else MARINE for d in order_days])
    ax.set_title("Pola Order per Hari (Kamis tersibuk, Sabtu hampir kosong)")
    ax.set_ylabel("Jumlah order")
    fig.tight_layout(); fig.savefig(CHART_DIR / "06_weekday_pattern.png"); plt.close(fig)

    # ---------- 07 distribusi nilai order ----------
    vals = orders["order_revenue"]
    clip = vals.quantile(0.99)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.hist(vals[vals <= clip], bins=50, color=MARINE, alpha=0.85)
    ax.axvline(vals.median(), color=TANGERINE, linewidth=2, label=f"Median {fmt_gbp(vals.median())}")
    ax.axvline(vals.mean(), color=GREEN, linewidth=2, linestyle="--", label=f"Mean (AOV) {fmt_gbp(vals.mean())}")
    ax.set_title(f"Distribusi Nilai Order (dipotong di persentil 99 = {fmt_gbp(clip)} agar terbaca)")
    ax.set_xlabel("Nilai order (GBP)"); ax.set_ylabel("Jumlah order"); ax.legend()
    fig.tight_layout(); fig.savefig(CHART_DIR / "07_order_value_distribution.png"); plt.close(fig)

    # ---------- 08 AOV per bulan ----------
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.bar(monthly["year_month"], monthly["aov"], color=PLUM, alpha=0.85)
    ax.axhline(orders["order_revenue"].mean(), color=TANGERINE, linestyle="--",
               label=f"AOV keseluruhan {fmt_gbp(orders['order_revenue'].mean())}")
    ax.set_title("Average Order Value per Bulan")
    ax.set_ylabel("AOV (GBP)"); ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout(); fig.savefig(CHART_DIR / "08_aov_by_month.png"); plt.close(fig)

    # ---------- 09 UK vs non-UK ----------
    uk_rev = df.loc[df["country"] == "United Kingdom", "revenue_gbp"].sum()
    nonuk_rev = df["revenue_gbp"].sum() - uk_rev
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.pie([uk_rev, nonuk_rev], labels=[f"United Kingdom\n{uk_rev / (uk_rev + nonuk_rev) * 100:.2f}%",
                                        f"Non-UK (42 negara)\n{nonuk_rev / (uk_rev + nonuk_rev) * 100:.2f}%"],
           colors=[MARINE, TANGERINE], autopct=lambda p: fmt_gbp(p / 100 * (uk_rev + nonuk_rev)),
           pctdistance=0.78, wedgeprops=dict(width=0.42, edgecolor="white"))
    ax.set_title("Share Revenue: United Kingdom vs Non-UK")
    fig.tight_layout(); fig.savefig(CHART_DIR / "09_uk_vs_nonuk_share.png"); plt.close(fig)

    # ---------- 10 konsentrasi order besar ----------
    big = orders[orders["order_revenue"] > 10000]
    small = orders[orders["order_revenue"] <= 10000]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    axes[0].bar(["≤ £10.000", "> £10.000"], [len(small), len(big)], color=[GREY, TANGERINE])
    axes[0].set_title("Jumlah order"); axes[0].set_ylabel("Order")
    for i, v in enumerate([len(small), len(big)]):
        axes[0].text(i, v * 1.02, f"{v:,}", ha="center", fontsize=10)
    axes[0].set_ylim(0, len(small) * 1.18)
    axes[1].bar(["≤ £10.000", "> £10.000"], [small["order_revenue"].sum(), big["order_revenue"].sum()], color=[GREY, TANGERINE])
    axes[1].set_title("Revenue (93 order besar = 8,87% revenue)")
    for i, v in enumerate([small["order_revenue"].sum(), big["order_revenue"].sum()]):
        axes[1].text(i, v * 1.02, fmt_gbp(v), ha="center", fontsize=10)
    axes[1].set_ylim(0, small["order_revenue"].sum() * 1.18)
    fig.suptitle("Konsentrasi Order Besar (> £10.000)", fontweight="bold")
    fig.tight_layout(); fig.savefig(CHART_DIR / "10_large_order_concentration.png"); plt.close(fig)

    # ---------- customer repeat summary (file data baru) ----------
    cust = orders.dropna(subset=["customer_id"]).copy()
    cust_dates = df.dropna(subset=["customer_id"]).groupby("customer_id")["invoice_date"].agg(["min", "max"])
    repeat_summary = cust.groupby("customer_id").agg(
        total_orders=("invoice", "nunique"),
        total_revenue_gbp=("order_revenue", "sum"),
        total_items=("order_items", "sum"),
    ).reset_index()
    repeat_summary["first_order_date"] = repeat_summary["customer_id"].map(cust_dates["min"]).dt.strftime("%Y-%m-%d")
    repeat_summary["last_order_date"] = repeat_summary["customer_id"].map(cust_dates["max"]).dt.strftime("%Y-%m-%d")
    repeat_summary["segment"] = np.where(repeat_summary["total_orders"] >= 2, "repeat", "one-time")
    repeat_summary = repeat_summary.round({"total_revenue_gbp": 2}).sort_values("total_revenue_gbp", ascending=False)
    repeat_summary.to_csv(ROOT / "data" / "customer_repeat_summary.csv", index=False)

    # ---------- 11 repeat vs one-time ----------
    seg = repeat_summary.groupby("segment").agg(customers=("customer_id", "nunique"), revenue=("total_revenue_gbp", "sum"))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    order_seg = ["repeat", "one-time"]
    colors = [GREEN, GREY]
    axes[0].bar(["Repeat (≥2 order)", "One-time (1 order)"], [seg.loc[s, "customers"] for s in order_seg], color=colors)
    axes[0].set_title("Jumlah customer teridentifikasi")
    for i, s in enumerate(order_seg):
        axes[0].text(i, seg.loc[s, "customers"] * 1.02, f"{int(seg.loc[s, 'customers']):,}", ha="center")
    axes[0].set_ylim(0, seg["customers"].max() * 1.2)
    axes[1].bar(["Repeat (≥2 order)", "One-time (1 order)"], [seg.loc[s, "revenue"] for s in order_seg], color=colors)
    axes[1].set_title("Revenue per segment")
    for i, s in enumerate(order_seg):
        axes[1].text(i, seg.loc[s, "revenue"] * 1.02, fmt_gbp(seg.loc[s, "revenue"]), ha="center")
    axes[1].set_ylim(0, seg["revenue"].max() * 1.2)
    fig.suptitle("Repeat Customer (72,39%) vs One-Time Customer", fontweight="bold")
    fig.tight_layout(); fig.savefig(CHART_DIR / "11_repeat_vs_onetime.png"); plt.close(fig)

    # ---------- 12 heatmap bulan x tahun ----------
    pivot = seas_g.reindex(index=range(1, 13), columns=[2009, 2010, 2011]).fillna(0)
    pivot.index = month_names
    pivot.columns = ["2009", "2010", "2011"]
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="YlGnBu", ax=ax,
                cbar_kws={"label": "Revenue (GBP)"})
    ax.set_title("Heatmap Revenue: Bulan x Tahun\n(2009 hanya Desember; 2011 sampai 9 Desember)")
    ax.set_xlabel("Tahun"); ax.set_ylabel("Bulan")
    fig.tight_layout(); fig.savefig(CHART_DIR / "12_heatmap_month_year.png"); plt.close(fig)

    # ---------- verifikasi terhadap findings.json ----------
    total_rev = round(df["revenue_gbp"].sum(), 2)
    print(f"Total revenue terhitung: £{total_rev:,.2f}")
    print(f"Total order: {df['invoice'].nunique():,} | Customer teridentifikasi: {df['customer_id'].nunique():,}")
    for p in FINDINGS_CANDIDATES:
        if p.exists():
            f = json.loads(p.read_text())
            ok_rev = abs(total_rev - f["total_revenue_gbp"]) < 0.01
            ok_ord = df["invoice"].nunique() == f["total_orders"]
            print(f"Cek findings.json ({p.name}): revenue cocok={ok_rev}, orders cocok={ok_ord}")
            break
    print(f"Chart dibuat: {len(list(CHART_DIR.glob('*.png')))} file di {CHART_DIR}")
    print(f"customer_repeat_summary.csv: {len(repeat_summary):,} baris customer")


if __name__ == "__main__":
    main()
