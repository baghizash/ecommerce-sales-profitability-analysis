"""
Cleaning Online Retail II (UCI) -> data/online_retail_ii_clean.csv

Aturan cleaning (lihat README.md dan data/SOURCES.md untuk alasan lengkap):
  1. Gabung dua sheet (Year 2009-2010 + Year 2010-2011).
  2. Buang duplikat persis (semua 8 kolom asli sama).
  3. Buang invoice batal/retur: Invoice diawali huruf 'C'.
  4. Buang Quantity <= 0 (sisa baris negatif adalah koreksi stok/rusak/hilang
     berketerangan seperti 'damages', 'lost', 'mixed' - bukan penjualan).
  5. Buang Price <= 0 (harga nol/negatif bukan transaksi penjualan valid).
  6. Customer ID kosong DIPERTAHANKAN: transaksinya penjualan nyata, membuangnya
     menghilangkan ~15% revenue dan mengecilkan total sales. Baris ini hanya
     dikeluarkan dari hitungan customer unik / analisis per customer.
  7. Description kosong dipertahankan (StockCode tetap valid); untuk ranking
     produk, Description diisi label terbanyak (modus) per StockCode.

Revenue = Quantity x Price, hanya untuk baris hasil langkah 1-5 di atas.
Tidak ada kolom cost di dataset ini, jadi profit margin TIDAK dihitung.

Raw xlsx TIDAK disimpan di repo ini (44 MB). Taruh di luar repo, contoh:
  ~/workspace/ecommerce-raw/online_retail_II.xlsx
Unduh: https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
"""
import json, sys
from pathlib import Path
import pandas as pd

DEFAULT_RAW = Path.home() / "workspace" / "ecommerce-raw" / "online_retail_II.xlsx"
OUT = Path(__file__).resolve().parent.parent / "data" / "online_retail_ii_clean.csv"

def main(raw_path: Path) -> None:
    xls = pd.ExcelFile(raw_path)
    frames = [pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names]
    raw = pd.concat(frames, ignore_index=True)
    raw.columns = [c.strip() for c in raw.columns]
    log = {"raw_rows": int(len(raw))}

    raw["Invoice"] = raw["Invoice"].astype(str)
    raw["StockCode"] = raw["StockCode"].astype(str)
    raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"])

    df = raw.drop_duplicates()
    log["dropped_exact_duplicates"] = int(log["raw_rows"] - len(df))

    before = len(df)
    df = df[~df["Invoice"].str.startswith("C")]
    log["dropped_cancelled_invoice_C"] = int(before - len(df))

    before = len(df)
    df = df[df["Quantity"] > 0]
    log["dropped_quantity_le_0"] = int(before - len(df))

    before = len(df)
    df = df[df["Price"] > 0]
    log["dropped_price_le_0"] = int(before - len(df))

    log["clean_rows"] = int(len(df))
    log["rows_missing_customer_id_kept"] = int(df["Customer ID"].isna().sum())
    log["rows_missing_description_kept"] = int(df["Description"].isna().sum())

    clean = pd.DataFrame({
        "invoice": df["Invoice"],
        "stock_code": df["StockCode"],
        "description": df["Description"],
        "quantity": df["Quantity"].astype(int),
        "invoice_date": df["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "price_gbp": df["Price"].round(2),
        "customer_id": df["Customer ID"].astype("Int64"),
        "country": df["Country"],
    })
    clean["revenue_gbp"] = (clean["quantity"] * clean["price_gbp"]).round(2)
    clean = clean.sort_values(["invoice_date", "invoice", "stock_code"]).reset_index(drop=True)
    clean.to_csv(OUT, index=False)
    log_path = OUT.parent / "cleaning_log.json"
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(log)
    print(f"clean csv -> {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")

if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RAW)
