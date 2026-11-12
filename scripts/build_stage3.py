#!/usr/bin/env python3
"""
Build Tahap 3 proyek E-Commerce Sales Performance & Profitability.

Menghasilkan (semua di ~/workspace/ecommerce-stage3/):
- powerbi/fact_sales.csv          : star schema, grain 1 baris = 1 invoice x 1 produk
- powerbi/dim_product.csv         : StockCode -> Description (modus) + flag merchandise
- powerbi/dim_customer.csv        : Customer ID + sentinel 0 = tidak teridentifikasi
- powerbi/dim_country.csv         : negara + flag UK
- powerbi/dim_date.csv            : tanggal, bulan, hari
- powerbi/measure_verification.csv: setiap measure dihitung dari fact dan
                                    dibandingkan dengan findings.json
- powerbi/dashboard_preview_halaman1.png
- charts/monthly_revenue_trend.png, charts/top10_products_revenue.png
- Portofolio-Ecommerce-Sales-Performance.pptx (10 slide, 16:9)
- Modul-Ecommerce-Sales-Performance.pdf

Sumber angka satu-satunya: findings.json Tahap 1 (terverifikasi dua cara).
Data bersih dibaca dari repo utama, TIDAK disalin ke staging.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path.home() / "workspace/ecommerce-sales-profitability"
STAGE = Path.home() / "workspace/ecommerce-stage3"
FIND = json.loads((REPO / "findings.json").read_text())

MARINE = "#14406B"
MARINE_LIGHT = "#2E6DA4"
BUTTER = "#F2C94C"
RED = "#D64541"
GREY = "#5D6D7E"
LIGHT_BG = "#F4F6F7"


def fmt_gbp(v, decimals=2):
    """Format Inggris -> gaya Indonesia: 20476260.43 -> £20.476.260,43"""
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "£" + s


def fmt_num(v):
    return f"{v:,}".replace(",", ".")


# ---------------------------------------------------------------- star schema
def build_star_schema():
    clean = pd.read_csv(
        REPO / "data/online_retail_ii_clean.csv",
        dtype={"stock_code": str, "invoice": str},
        parse_dates=["invoice_date"],
    )
    clean["customer_id"] = clean["customer_id"].fillna(0).astype(int)
    clean["date"] = clean["invoice_date"].dt.date
    clean["hour"] = clean["invoice_date"].dt.hour

    # fact: grain invoice x produk (baris transaksi yang produknya sama dalam
    # satu invoice digabung; quantity dan revenue dijumlahkan)
    fact = (
        clean.groupby(["invoice", "stock_code"], as_index=False)
        .agg(
            customer_id=("customer_id", "first"),
            country=("country", "first"),
            date=("date", "first"),
            hour=("hour", "first"),
            quantity=("quantity", "sum"),
            revenue_gbp=("revenue_gbp", "sum"),
        )
        .rename(columns={"date": "invoice_date"})
    )
    fact["revenue_gbp"] = fact["revenue_gbp"].round(2)
    fact = fact[
        ["invoice", "stock_code", "customer_id", "country",
         "invoice_date", "hour", "quantity", "revenue_gbp"]
    ].sort_values(["invoice_date", "invoice", "stock_code"])
    fact.to_csv(STAGE / "powerbi/fact_sales.csv", index=False)

    # dim_product: description modus per stock code
    desc = (
        clean.groupby("stock_code")["description"]
        .agg(lambda s: s.mode().iat[0] if len(s.mode()) else "")
        .rename("description")
    )
    dim_product = desc.reset_index()
    dim_product["is_merchandise"] = np.where(
        dim_product["stock_code"].str[0].str.isdigit(), "Ya", "Tidak"
    )
    dim_product.to_csv(STAGE / "powerbi/dim_product.csv", index=False)

    # dim_customer: semua customer teridentifikasi + sentinel 0
    cust_ids = sorted(clean.loc[clean["customer_id"] != 0, "customer_id"].unique())
    dim_customer = pd.DataFrame(
        {"customer_id": [0] + cust_ids,
         "is_identified": ["Tidak"] + ["Ya"] * len(cust_ids)}
    )
    dim_customer.to_csv(STAGE / "powerbi/dim_customer.csv", index=False)

    # dim_country
    countries = sorted(clean["country"].unique())
    dim_country = pd.DataFrame(
        {"country": countries,
         "is_uk": ["Ya" if c == "United Kingdom" else "Tidak" for c in countries]}
    )
    dim_country.to_csv(STAGE / "powerbi/dim_country.csv", index=False)

    # dim_date
    dates = pd.DataFrame({"date": sorted(clean["date"].unique())})
    dt = pd.to_datetime(dates["date"])
    month_names = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November",
                   "Desember"]
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                     "Saturday", "Sunday"]
    dates["year"] = dt.dt.year
    dates["month"] = dt.dt.month
    dates["month_name"] = [month_names[m - 1] for m in dates["month"]]
    dates["year_month"] = dt.dt.strftime("%Y-%m")
    dates["weekday"] = [weekday_names[d] for d in dt.dt.weekday]
    dates["day"] = dt.dt.day
    dates.to_csv(STAGE / "powerbi/dim_date.csv", index=False)

    return fact, dim_product, dim_customer, dim_country, dates


# ---------------------------------------------------------------- verification
def verify(fact):
    fact = fact.copy()
    fact["year_month"] = pd.to_datetime(fact["invoice_date"]).dt.strftime("%Y-%m")
    total_rev = round(fact["revenue_gbp"].sum(), 2)
    total_orders = fact["invoice"].nunique()
    total_units = int(fact["quantity"].sum())
    total_customers = fact.loc[fact["customer_id"] != 0, "customer_id"].nunique()
    uk_rev = round(fact.loc[fact["country"] == "United Kingdom",
                            "revenue_gbp"].sum(), 2)
    monthly = fact.groupby("year_month")["revenue_gbp"].sum()
    best_month_rev = round(monthly.max(), 2)
    # ranking produk di findings hanya untuk merchandise (StockCode berawalan
    # digit); kode POST dan sejenisnya adalah ongkir, bukan produk
    top_prod_rev = round(
        fact.loc[fact["stock_code"] == "22423", "revenue_gbp"].sum(), 2)
    no_cust_rev = round(
        fact.loc[fact["customer_id"] == 0, "revenue_gbp"].sum(), 2)

    rows = [
        ("Total Revenue", total_rev, FIND["total_revenue_gbp"], 0.05),
        ("Total Orders", total_orders, FIND["total_orders"], 0),
        ("Average Order Value", round(total_rev / total_orders, 2),
         FIND["average_order_value_gbp"], 0.01),
        ("Total Units", total_units, FIND["total_units_sold"], 0),
        ("Basket Size (unit per order)", round(total_units / total_orders, 2),
         FIND["basket_size_items_per_order_mean"], 0.01),
        ("Total Customers Teridentifikasi", total_customers,
         FIND["total_customers_identified"], 0),
        ("UK Revenue", uk_rev, 17410196.10, 0.05),
        ("UK Revenue Share %", round(uk_rev / total_rev * 100, 2),
         FIND["uk_revenue_share_pct"], 0.01),
        ("Revenue Bulan Terbaik (Nov 2011)", best_month_rev,
         FIND["best_month"]["revenue_gbp"], 0.05),
        ("Revenue Produk Teratas (22423)", top_prod_rev,
         FIND["top10_products_by_revenue"][0]["revenue_gbp"], 0.05),
        ("Revenue Tanpa Customer ID", no_cust_rev,
         FIND["revenue_without_customer_id_gbp"], 0.05),
        ("Jumlah Baris Fact (invoice x produk)", len(fact), None, None),
    ]
    out = []
    for name, got, want, tol in rows:
        if want is None:
            out.append([name, got, "", "", "INFO GRAIN"])
        else:
            diff = round(abs(got - want), 4)
            out.append([name, got, want, diff,
                        "COCOK" if diff <= tol else "TIDAK COCOK"])
    ver = pd.DataFrame(out, columns=[
        "measure", "nilai_dari_fact_sales", "nilai_findings_tahap1",
        "selisih", "status"])
    ver.to_csv(STAGE / "powerbi/measure_verification.csv", index=False)
    return ver


# ---------------------------------------------------------------- charts
def build_charts():
    monthly = pd.DataFrame(FIND["monthly_sales"])
    plt.rcParams.update({"font.size": 11, "axes.edgecolor": GREY})

    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = range(len(monthly))
    ax.plot(x, monthly["revenue_gbp"] / 1e6, color=MARINE, lw=2.4,
            marker="o", ms=4)
    ax.fill_between(x, monthly["revenue_gbp"] / 1e6, color=MARINE, alpha=0.08)
    peak = monthly["revenue_gbp"].idxmax()
    ax.annotate("Puncak: Nov 2011\n£1.503.866,78",
                xy=(peak, monthly.loc[peak, "revenue_gbp"] / 1e6),
                xytext=(peak - 7.5, 1.62), fontsize=10, color=MARINE,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=MARINE))
    labels = [ym[2:] for ym in monthly["year_month"]]
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), 2)],
                       rotation=45, ha="left", fontsize=9)
    ax.set_ylabel("Revenue (juta £)")
    ax.set_title("Revenue bulanan, Des 2009 - Des 2011 (parsial)",
                 color=MARINE, fontweight="bold", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(STAGE / "charts/monthly_revenue_trend.png", dpi=150)
    plt.close(fig)

    top = pd.DataFrame(FIND["top10_products_by_revenue"]).iloc[::-1]
    names = [d.title()[:38] for d in top["description"]]
    fig, ax = plt.subplots(figsize=(10, 5.0))
    bars = ax.barh(names, top["revenue_gbp"] / 1e3, color=MARINE_LIGHT)
    bars[9].set_color(MARINE)
    for b, v in zip(bars, top["revenue_gbp"]):
        ax.text(v / 1e3 + 6, b.get_y() + b.get_height() / 2,
                fmt_gbp(v, 0), va="center", fontsize=9)
    ax.set_xlim(0, 380)
    ax.set_xlabel("Revenue (ribu £)")
    ax.set_title("Top 10 produk by revenue, hanya 7,69% dari total revenue",
                 color=MARINE, fontweight="bold", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    fig.savefig(STAGE / "charts/top10_products_revenue.png", dpi=150)
    plt.close(fig)


def build_preview():
    monthly = pd.DataFrame(FIND["monthly_sales"])
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 2.4],
                          hspace=0.55, wspace=0.35,
                          left=0.05, right=0.97, top=0.84, bottom=0.07)
    fig.text(0.05, 0.945, "Executive Sales Overview",
             fontsize=24, fontweight="bold", color=MARINE)
    fig.text(0.05, 0.905,
             "E-Commerce Sales Performance & Profitability | Online Retail II, "
             "1 Des 2009 - 9 Des 2011",
             fontsize=12, color=GREY)

    cards = [
        ("Total Revenue", fmt_gbp(FIND["total_revenue_gbp"])),
        ("Total Orders", fmt_num(FIND["total_orders"])),
        ("Average Order Value", fmt_gbp(FIND["average_order_value_gbp"])),
        ("Basket Size", "279,59 unit/order"),
    ]
    for i, (label, value) in enumerate(cards):
        ax = fig.add_subplot(gs[0, i])
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                                   facecolor=LIGHT_BG, edgecolor=MARINE,
                                   lw=1.4))
        ax.text(0.5, 0.68, value, ha="center", fontsize=17,
                fontweight="bold", color=MARINE, transform=ax.transAxes)
        ax.text(0.5, 0.30, label, ha="center", fontsize=11.5, color=GREY,
                transform=ax.transAxes)

    ax = fig.add_subplot(gs[1, 0:3])
    x = range(len(monthly))
    ax.plot(x, monthly["revenue_gbp"] / 1e6, color=MARINE, lw=2.4,
            marker="o", ms=4)
    ax.fill_between(x, monthly["revenue_gbp"] / 1e6, color=MARINE, alpha=0.08)
    peak = monthly["revenue_gbp"].idxmax()
    ax.annotate("Nov 2011: £1.503.866,78",
                xy=(peak, monthly.loc[peak, "revenue_gbp"] / 1e6),
                xytext=(peak - 8, 1.60), fontsize=11, color=MARINE,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=MARINE))
    labels = [ym[2:] for ym in monthly["year_month"]]
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), 2)],
                       rotation=45, ha="left", fontsize=9)
    ax.set_ylabel("Revenue (juta £)")
    ax.set_title("Tren revenue bulanan", color=MARINE, fontweight="bold",
                 loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)

    ax = fig.add_subplot(gs[1, 3])
    ax.axis("off")
    notes = (
        "Catatan halaman ini\n\n"
        "• UK = 85,03% revenue\n"
        "  (£17.410.196,10; 43 negara).\n\n"
        "• 5.878 customer;\n"
        "  72,39% repeat purchase.\n\n"
        "• Des 2011 bulan parsial\n"
        "  (hanya sampai 9 Des),\n"
        "  bukan bulan penuh.\n\n"
        "• Bisnis wholesale: AOV\n"
        "  dan basket size jauh di\n"
        "  atas e-commerce consumer."
    )
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                               facecolor="#FFF8E1", edgecolor=BUTTER, lw=1.4))
    ax.text(0.06, 0.95, notes, va="top", fontsize=11, color="#333333",
            transform=ax.transAxes, linespacing=1.45)
    fig.savefig(STAGE / "powerbi/dashboard_preview_halaman1.png", dpi=110)
    plt.close(fig)


def build_ppt():
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    MAR = RGBColor(0x14, 0x40, 0x6B)
    MARL = RGBColor(0x2E, 0x6D, 0xA4)
    BUT = RGBColor(0xF2, 0xC9, 0x4C)
    WHT = RGBColor(0xFF, 0xFF, 0xFF)
    DRK = RGBColor(0x2B, 0x2B, 0x2B)
    GRY = RGBColor(0x5D, 0x6D, 0x7E)
    LGT = RGBColor(0xF4, 0xF6, 0xF7)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def bg(slide, color):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = color

    def box(slide, x, y, w, h, fill=None, line=None):
        from pptx.enum.shapes import MSO_SHAPE
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                    Inches(w), Inches(h))
        if fill is None:
            sh.fill.background()
        else:
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
        if line is None:
            sh.line.fill.background()
        else:
            sh.line.color.rgb = line
            sh.line.width = Pt(1)
        sh.shadow.inherit = False
        return sh

    def text(slide, x, y, w, h, s, size=18, color=DRK, bold=False,
             align=PP_ALIGN.LEFT, font="Calibri"):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w),
                                      Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = ln
            p.alignment = align
            for r in p.runs:
                r.font.size = Pt(size)
                r.font.bold = bold
                r.font.color.rgb = color
                r.font.name = font
        return tb

    def header(slide, title, sub=""):
        bg(slide, WHT)
        box(slide, 0, 0, 13.333, 1.05, fill=MAR)
        text(slide, 0.6, 0.22, 12.1, 0.6, title, size=27, color=WHT, bold=True)
        if sub:
            text(slide, 0.6, 1.25, 12.1, 0.5, sub, size=14, color=GRY)

    def bullets(slide, x, y, w, items, size=17, gap=0.62, color=DRK):
        yy = y
        for it in items:
            box(slide, x, yy + 0.13, 0.14, 0.14, fill=BUT)
            text(slide, x + 0.32, yy, w - 0.32, gap, it, size=size, color=color)
            yy += gap
        return yy

    # 1 - cover
    s = prs.slides.add_slide(blank)
    bg(s, MAR)
    box(s, 0, 5.55, 13.333, 0.14, fill=BUT)
    text(s, 0.8, 1.15, 11.8, 1.9,
         "E-Commerce Sales Performance\n& Profitability", size=44, color=WHT,
         bold=True)
    text(s, 0.8, 3.35, 11.8, 0.6,
         "Analisis penjualan wholesale giftware Inggris, 1 Des 2009 - 9 Des 2011",
         size=19, color=BUT)
    text(s, 0.8, 4.35, 11.8, 0.6,
         "Dataset Online Retail II (UCI) | 1.007.913 baris transaksi bersih",
         size=16, color=WHT)
    text(s, 0.8, 6.05, 11.8, 0.9,
         "BAGHIZ ASSHIDDIQIE ARASYA\nData Analyst | E-commerce / Retail Analyst",
         size=16, color=WHT)

    # 2 - ringkasan dan pertanyaan bisnis
    s = prs.slides.add_slide(blank)
    header(s, "Proyek ini menjawab pertanyaan bisnis, bukan sekadar membuat chart")
    bullets(s, 0.6, 1.5, 12.1, [
        "Berapa total revenue, order, dan customer selama dua tahun, dan bagaimana tren bulanannya?",
        "Produk dan negara mana yang menyumbang revenue terbesar?",
        "Seberapa besar nilai satu order (AOV dan basket size), dan seberapa terkonsentrasi revenue pada order besar?",
        "Kapan pola transaksi paling ramai: bulan, hari, dan jam apa?",
        "Berapa bagian customer yang kembali membeli (repeat purchase)?",
    ], size=17, gap=0.66)
    box(s, 0.6, 5.15, 12.13, 1.55, fill=LGT)
    text(s, 0.85, 5.35, 11.7, 1.2,
         "Metode: cleaning terdokumentasi (invoice batal, duplikat, quantity dan price tidak valid dibuang), "
         "analisis Python dan SQL, verifikasi angka dua cara independen (12 dari 12 cocok), "
         "lalu dashboard Power BI 4 halaman berbasis star schema.",
         size=15.5, color=DRK)

    # 3 - KPI cards
    s = prs.slides.add_slide(blank)
    header(s, "Angka kunci: revenue £20,48 juta dari 40.077 order",
           "Semua angka terverifikasi dua cara, pandas dan SQL")
    kpis = [
        ("Total Revenue", fmt_gbp(FIND["total_revenue_gbp"])),
        ("Total Orders", fmt_num(FIND["total_orders"])),
        ("Average Order Value", fmt_gbp(FIND["average_order_value_gbp"])),
        ("Basket Size", "279,59 unit/order"),
        ("Customer Teridentifikasi", fmt_num(FIND["total_customers_identified"])),
        ("Unit Terjual", fmt_num(FIND["total_units_sold"])),
    ]
    for i, (label, val) in enumerate(kpis):
        cx = 0.6 + (i % 3) * 4.18
        cy = 2.0 + (i // 3) * 2.15
        box(s, cx, cy, 3.85, 1.75, fill=LGT, line=MARL)
        text(s, cx + 0.2, cy + 0.28, 3.45, 0.7, val, size=23, color=MAR,
             bold=True, align=PP_ALIGN.CENTER)
        text(s, cx + 0.2, cy + 1.05, 3.45, 0.5, label, size=13.5, color=GRY,
             align=PP_ALIGN.CENTER)
    text(s, 0.6, 6.65, 12.1, 0.5,
         "Median nilai order £302,22 dan median basket 146 unit: distribusi order miring ke kanan, khas wholesale.",
         size=14, color=GRY)

    # 4 - tren bulanan
    s = prs.slides.add_slide(blank)
    header(s, "November adalah puncak di kedua tahun",
           "Pola pre-Christmas giftware yang konsisten")
    s.shapes.add_picture(str(STAGE / "charts/monthly_revenue_trend.png"),
                         Inches(0.6), Inches(1.95), width=Inches(8.4))
    bullets(s, 9.3, 2.1, 3.55, [
        "Nov 2011: £1.503.866,78 dari 2.769 order, bulan terbaik.",
        "Nov 2010 hampir sama: £1.464.293,14.",
        "Des 2011 parsial (sampai 9 Des), tidak dibandingkan sebagai bulan penuh.",
    ], size=14.5, gap=1.28)

    # 5 - produk
    s = prs.slides.add_slide(blank)
    header(s, "Revenue tersebar: top 10 produk hanya 7,69%",
           "Tidak bergantung pada sedikit produk unggulan")
    s.shapes.add_picture(str(STAGE / "charts/top10_products_revenue.png"),
                         Inches(0.6), Inches(1.95), width=Inches(8.4))
    bullets(s, 9.3, 2.1, 3.55, [
        "Teratas: Regency Cakestand 3 Tier, £330.590,32.",
        "Ranking hanya produk merchandise; kode ongkir dan voucher dikeluarkan.",
        "Satu produk viral dari 1 order raksasa: Paper Craft, £168.469,60.",
    ], size=14.5, gap=1.28)

    # 6 - geografi
    s = prs.slides.add_slide(blank)
    header(s, "UK mendominasi 85,03%, sisanya terkonsentrasi di Eropa Barat")
    rows = [("United Kingdom", "£17.410.196,10", "36.535 order"),
            ("EIRE", "£658.767,31", "hanya 5 customer"),
            ("Netherlands", "£554.038,09", "228 order"),
            ("Germany", "£425.019,71", "789 order"),
            ("France", "£350.456,09", "622 order"),
            ("Australia", "£169.283,46", "pasar non-Eropa terbesar")]
    yy = 1.65
    for name, rev, note in rows:
        box(s, 0.6, yy, 12.13, 0.72, fill=LGT if rows.index((name, rev, note)) % 2 == 0 else WHT)
        text(s, 0.85, yy + 0.17, 3.6, 0.45, name, size=16.5, color=MAR, bold=True)
        text(s, 4.6, yy + 0.17, 3.2, 0.45, rev, size=16.5, color=DRK)
        text(s, 8.0, yy + 0.17, 4.4, 0.45, note, size=14.5, color=GRY)
        yy += 0.86
    text(s, 0.6, 6.9, 12.1, 0.4,
         "Total 43 negara. Risiko konsentrasi: ketergantungan besar pada pasar domestik UK.",
         size=14, color=GRY)

    # 7 - customer
    s = prs.slides.add_slide(blank)
    header(s, "Repeat purchase kuat: 72,39% customer kembali membeli")
    bullets(s, 0.6, 1.6, 7.6, [
        "4.255 dari 5.878 customer teridentifikasi punya 2 order atau lebih.",
        "Median 3 order per customer: basis pelanggan wholesale yang loyal.",
        "Tapi 15,15% revenue (£3.101.456,18 dari 3.108 order) tidak punya Customer ID.",
        "Artinya analisis customer hanya mencakup sekitar 85% revenue.",
    ], size=16.5, gap=0.95)
    box(s, 8.6, 1.7, 4.1, 3.1, fill=MAR)
    text(s, 8.85, 1.95, 3.6, 2.6,
         "Insight\n\nLoyalitas tinggi bukan masalah utama bisnis ini. Masalah datanya: "
         "sebagian revenue besar tidak bisa diatribusikan ke customer mana pun.",
         size=15.5, color=WHT)
    text(s, 0.6, 5.9, 12.1, 0.6,
         "Rekomendasi: perbaiki pencatatan Customer ID di titik transaksi sebelum menjalankan program loyalitas berbasis data.",
         size=15, color=MAR)

    # 8 - pola waktu
    s = prs.slides.add_slide(blank)
    header(s, "Pola waktu mengikuti jam kerja, bukan pola belanja consumer")
    bullets(s, 0.6, 1.6, 12.1, [
        "Jam puncak pukul 12.00: 6.427 order, £2.850.377,67. Hampir semua aktivitas di rentang 08.00 sampai 17.00.",
        "Hari tersibuk Thursday: 8.288 order, £4.195.212,76.",
        "Saturday hampir kosong: hanya 30 order (£9.803,05), sementara Sunday justru ramai dengan 4.835 order.",
        "Pola ini konsisten dengan pembeli wholesale yang bertransaksi di hari dan jam kerja.",
    ], size=16.5, gap=0.98)
    box(s, 0.6, 5.85, 12.13, 1.05, fill=LGT)
    text(s, 0.85, 6.05, 11.7, 0.7,
         "Implikasi operasional: dukungan penjualan dan kesiapan stok paling kritis di tengah hari kerja, terutama Kamis dan musim November.",
         size=15.5, color=DRK)

    # 9 - kualitas revenue dan keterbatasan
    s = prs.slides.add_slide(blank)
    header(s, "Kualitas revenue dan batas analisis, dinyatakan apa adanya")
    bullets(s, 0.6, 1.6, 12.1, [
        "93 order di atas £10.000 menyumbang 8,87% revenue: revenue sensitif terhadap sedikit order wholesale besar.",
        "Order terbesar tunggal £168.469,60 (invoice 581483, 80.995 unit, 9 Des 2011).",
        "Dataset tidak punya kolom cost, jadi gross profit dan margin TIDAK dihitung dan tidak dikarang.",
        "Sisi profitability yang diukur: AOV, basket size, konsentrasi order besar, repeat purchase, pangsa produk dan negara.",
        "Desember 2011 parsial dan karakter wholesale membatasi perbandingan dengan e-commerce consumer.",
    ], size=16, gap=0.88)

    # 10 - penutup
    s = prs.slides.add_slide(blank)
    bg(s, MAR)
    box(s, 0, 1.55, 13.333, 0.14, fill=BUT)
    text(s, 0.8, 0.55, 11.8, 0.8, "Kesimpulan untuk posisi E-commerce / Retail Analyst",
         size=28, color=WHT, bold=True)
    bullets_txt = [
        "Dashboard 4 halaman memisahkan executive overview, product & country, customer & order pattern, dan data quality.",
        "Skill yang ditunjukkan: SQL, Python (pandas), Power BI (star schema dan DAX), data cleaning, dan data storytelling.",
        "Semua angka di deck ini sama dengan findings terverifikasi di repo: github.com/baghizash/ecommerce-sales-profitability-analysis",
    ]
    yy = 2.15
    for it in bullets_txt:
        box(s, 0.8, yy + 0.12, 0.14, 0.14, fill=BUT)
        text(s, 1.12, yy, 11.3, 0.95, it, size=17, color=WHT)
        yy += 1.08
    text(s, 0.8, 6.35, 11.8, 0.6,
         "BAGHIZ ASSHIDDIQIE ARASYA | Data Analyst", size=16, color=BUT)

    prs.save(STAGE / "Portofolio-Ecommerce-Sales-Performance.pptx")


def build_module():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=19,
                        textColor=colors.HexColor(MARINE), spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14.5,
                        textColor=colors.HexColor(MARINE), spaceBefore=12,
                        spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=11,
                          leading=16, alignment=4, spaceAfter=7)
    bull = ParagraphStyle("bull", parent=body, leftIndent=14, bulletIndent=4,
                          spaceAfter=4)
    small = ParagraphStyle("small", parent=body, fontSize=9.5,
                           textColor=colors.HexColor(GREY))

    story = []
    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph("Modul Belajar", ParagraphStyle(
        "k", parent=body, fontSize=13, textColor=colors.HexColor(GREY))))
    story.append(Paragraph("E-Commerce Sales Performance &amp; Profitability",
                           ParagraphStyle("t", parent=h1, fontSize=25,
                                          leading=32)))
    story.append(Paragraph(
        "Memahami analisis penjualan e-commerce dari data transaksi asli: "
        "cleaning, KPI, star schema, dan cara membaca temuan seperti seorang "
        "Retail Analyst.", body))
    story.append(Spacer(1, 0.7 * cm))
    story.append(Paragraph(
        "Dataset: Online Retail II (UCI Machine Learning Repository), "
        "1.007.913 baris transaksi bersih, 1 Desember 2009 sampai 9 Desember 2011.<br/>"
        "Penulis: BAGHIZ ASSHIDDIQIE ARASYA", small))
    story.append(PageBreak())

    story.append(Paragraph("Bab 1. Apa yang Dilakukan Retail Analyst", h1))
    story.append(Paragraph(
        "Retail Analyst mengubah data transaksi menjadi keputusan: produk apa "
        "yang dijaga stoknya, pasar mana yang dikembangkan, dan kapan tim "
        "penjualan harus bersiap menghadapi lonjakan. Di proyek ini datanya "
        "berasal dari perusahaan giftware online di Inggris yang pelanggannya "
        "banyak wholesaler, jadi ukuran ordernya jauh lebih besar daripada "
        "belanja ritel satuan.", body))
    story.append(Paragraph(
        "Pertanyaan bisnis yang dijawab: berapa total revenue dan trennya, "
        "produk dan negara penyumbang terbesar, berapa nilai rata-rata satu "
        "order, kapan transaksi paling ramai, dan berapa banyak customer yang "
        "kembali membeli.", body))

    story.append(Paragraph("Bab 2. KPI yang Wajib Dipahami Pemula", h1))
    kpi_data = [
        ["KPI", "Arti", "Nilai di proyek ini"],
        ["Revenue", "Quantity x Price untuk transaksi valid",
         fmt_gbp(FIND["total_revenue_gbp"])],
        ["Order", "Satu nomor invoice unik, bukan invoice batal", "40.077"],
        ["Average Order Value", "Revenue dibagi jumlah order",
         fmt_gbp(FIND["average_order_value_gbp"])],
        ["Basket Size", "Unit terjual dibagi jumlah order", "279,59 unit/order"],
        ["Repeat Purchase", "Pangsa customer dengan 2 order atau lebih", "72,39%"],
    ]
    t = Table(kpi_data, colWidths=[3.6 * cm, 6.9 * cm, 5.2 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(MARINE)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(GREY)),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Paragraph(
        "Catatan penting: dataset ini tidak memiliki kolom cost, sehingga "
        "profit margin tidak bisa dihitung. Analyst yang baik menyatakan batas "
        "ini dengan jelas, bukan mengarang angka margin.", body))
    story.append(PageBreak())

    story.append(Paragraph("Bab 3. Cleaning: Bagian yang Menentukan Kualitas", h1))
    story.append(Paragraph(
        "Dari 1.067.371 baris mentah, yang dibuang adalah 34.335 duplikat "
        "persis, 19.104 baris invoice batal (diawali huruf C), 3.393 baris "
        "quantity tidak valid, dan 2.626 baris price tidak valid. Sisa data "
        "bersih 1.007.913 baris.", body))
    story.append(Paragraph(
        "Dua keputusan yang disengaja. Pertama, baris tanpa Customer ID "
        "dipertahankan karena transaksinya nyata; membuangnya menghapus "
        "revenue " + fmt_gbp(FIND["revenue_without_customer_id_gbp"]) +
        " atau 15,15% dari total. Kedua, ranking produk hanya memakai "
        "StockCode berawalan digit, karena kode seperti POST dan BANK CHARGES "
        "adalah ongkir dan penyesuaian, bukan produk.", body))
    story.append(Paragraph(
        "Setiap angka kunci kemudian diverifikasi dua cara independen, "
        "agregasi pandas dan SQL lewat SQLite. Di Tahap 1 hasilnya 12 dari 12 "
        "cocok, dan di Tahap 3 measure Power BI dihitung ulang dari fact "
        "table dengan hasil yang sama persis.", body))

    story.append(Paragraph("Bab 4. Star Schema untuk Power BI", h1))
    story.append(Paragraph(
        "Dashboard memakai star schema: satu fact_sales di tengah dan empat "
        "tabel dimensi di sekelilingnya. Grain fact_sales adalah satu baris "
        "untuk satu invoice kali satu produk (996.548 baris), berisi quantity "
        "dan revenue. Dimensinya adalah dim_product, dim_customer, "
        "dim_country, dan dim_date.", body))
    story.append(Paragraph(
        "Kenapa grain-nya bukan baris transaksi mentah? Karena baris yang "
        "produknya sama dalam satu invoice bisa digabung tanpa mengubah "
        "revenue, order, maupun unit sama sekali, dan ukuran file jauh lebih "
        "masuk akal untuk disimpan. Customer tanpa ID diberi kode sentinel 0 "
        "di dim_customer supaya tidak ada baris fact yang kehilangan relasi.", body))
    story.append(PageBreak())

    story.append(Paragraph("Bab 5. Temuan Utama dan Cara Membacanya", h1))
    for txt in [
        "<b>Musim mengalahkan bulan biasa.</b> November menjadi puncak di "
        "kedua tahun; November 2011 mencapai " +
        fmt_gbp(FIND["best_month"]["revenue_gbp"]) +
        ". Untuk bisnis giftware, persiapan stok dan promosi harus selesai "
        "sebelum Oktober berakhir.",
        "<b>Pasar sangat terkonsentrasi secara geografi.</b> UK menyumbang "
        "85,03% revenue. Di luar UK, EIRE terbesar (" +
        fmt_gbp(658767.31) + ") tetapi hanya dari 5 customer, jadi angka "
        "besar itu rapuh.",
        "<b>Produk justru tidak terkonsentrasi.</b> Top 10 produk hanya "
        "7,69% revenue. Produk teratas Regency Cakestand 3 Tier menghasilkan " +
        fmt_gbp(330590.32) + ", jauh di bawah 2% total revenue.",
        "<b>Customer loyal, data customer berlubang.</b> 72,39% customer "
        "membeli ulang dengan median 3 order, tetapi 15,15% revenue tidak "
        "punya Customer ID sehingga tidak bisa dianalisis per customer.",
        "<b>Ritme wholesale.</b> Puncak order pukul 12.00 dan hari tersibuk "
        "Thursday (8.288 order), sedangkan Saturday hanya 30 order. Ini pola "
        "transaksi jam kerja, bukan belanja malam ala consumer.",
    ]:
        story.append(Paragraph(txt, bull, bulletText="•"))
    story.append(Image(str(STAGE / "charts/monthly_revenue_trend.png"),
                       width=16.5 * cm, height=6.93 * cm))
    story.append(Paragraph(
        "Gambar: tren revenue bulanan. Perhatikan penurunan Desember 2011 "
        "bukan kemerosotan bisnis, melainkan data yang berakhir 9 Desember.",
        small))
    story.append(PageBreak())

    story.append(Paragraph("Bab 6. Latihan untuk Pembaca", h1))
    for txt in [
        "Hitung average order value bulan Oktober 2011 dari tabel monthly "
        "sales (revenue " + fmt_gbp(1151263.73) + ", 2.040 order) dan "
        "bandingkan dengan AOV keseluruhan " +
        fmt_gbp(FIND["average_order_value_gbp"]) + ".",
        "Jelaskan dengan kalimatmu sendiri kenapa basket size 279,59 unit "
        "tidak bisa dibandingkan langsung dengan toko online consumer.",
        "Kalau Customer ID yang kosong berhasil dilengkapi, analisis baru apa "
        "saja yang menjadi mungkin? Sebutkan minimal dua.",
        "Susun satu rekomendasi operasional dari pola jam dan hari, lengkap "
        "dengan angka pendukungnya.",
    ]:
        story.append(Paragraph(txt, bull, bulletText="•"))
    story.append(Paragraph("Glosarium Singkat", h2))
    for txt in [
        "<b>Star schema:</b> susunan tabel fact dan dimensi untuk dashboard.",
        "<b>Grain:</b> satu baris di tabel mewakili apa, dinyatakan eksplisit.",
        "<b>DAX:</b> bahasa rumus untuk measure di Power BI.",
        "<b>Measure:</b> hitungan yang mengikuti filter dashboard, misalnya "
        "Total Revenue dan Average Order Value.",
        "<b>Sentinel:</b> nilai khusus pengganti data kosong, di proyek ini "
        "customer 0 berarti tidak teridentifikasi.",
    ]:
        story.append(Paragraph(txt, bull, bulletText="•"))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Seluruh angka modul ini berasal dari findings.json proyek yang "
        "terverifikasi dua cara. Repo: github.com/baghizash/"
        "ecommerce-sales-profitability-analysis", small))

    doc = SimpleDocTemplate(
        str(STAGE / "Modul-Ecommerce-Sales-Performance.pdf"),
        pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="Modul E-Commerce Sales Performance & Profitability",
        author="BAGHIZ ASSHIDDIQIE ARASYA")
    doc.build(story)


if __name__ == "__main__":
    fact, *_ = build_star_schema()
    ver = verify(fact)
    print(ver.to_string(index=False))
    build_charts()
    build_preview()
    build_ppt()
    build_module()
    print("star schema + verifikasi + chart + preview + PPT + modul selesai")
