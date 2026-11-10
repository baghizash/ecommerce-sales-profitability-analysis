"""
Muat data/online_retail_ii_clean.csv ke SQLite (tabel sales_clean) supaya
sql/queries.sql bisa dijalankan. File .db TIDAK disimpan di repo:
default output ke /tmp/ecommerce_sales.db, hapus setelah selesai.
"""
import sqlite3, sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/ecommerce_sales.db")

def main() -> None:
    df = pd.read_csv(BASE / "data" / "online_retail_ii_clean.csv",
                     dtype={"invoice": str, "stock_code": str})
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as con:
        df.to_sql("sales_clean", con, index=False)
        con.execute("CREATE INDEX idx_invoice ON sales_clean(invoice)")
        con.execute("CREATE INDEX idx_country ON sales_clean(country)")
        con.execute("CREATE INDEX idx_stock ON sales_clean(stock_code)")
    print(f"sales_clean: {len(df)} rows -> {db_path}")

if __name__ == "__main__":
    main()
