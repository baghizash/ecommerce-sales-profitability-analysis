# Sumber Data

## Dataset utama: Online Retail II (UCI Machine Learning Repository)

- **Nama dataset:** Online Retail II
- **Penerbit:** UCI Machine Learning Repository, University of California Irvine
- **Halaman dataset:** https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **File unduhan resmi (dipakai di proyek ini):** https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
- **Tanggal unduh:** 8 November 2026
- **Isi arsip:** `online_retail_II.xlsx` (45.622.278 byte), 2 sheet:
  - `Year 2009-2010`: 525.461 baris transaksi
  - `Year 2010-2011`: 541.910 baris transaksi
  - Total baris mentah gabungan: **1.067.371**
- **Isi data:** semua transaksi sebuah perusahaan retail online berbasis di Inggris
  (menjual giftware, banyak customer adalah wholesaler) periode 1 Desember 2009
  sampai 9 Desember 2011. Kolom: Invoice, StockCode, Description, Quantity,
  InvoiceDate, Price (GBP), Customer ID, Country.
- **Sitasi:** Chen, D. (2015). Online Retail II [Dataset]. UCI Machine Learning
  Repository. https://doi.org/10.24432/C5CG6D
- **Lisensi:** Creative Commons Attribution 4.0 International (CC BY 4.0), sesuai
  halaman dataset UCI.

File xlsx mentah (44 MB) **tidak disimpan di repo ini**. Di mesin lokal ia berada
di luar folder repo (`~/workspace/ecommerce-raw/`) dan bisa diunduh ulang dari
tautan resmi di atas. Script `scripts/clean_data.py` membaca file itu dan
menghasilkan data bersih.

## File di folder data/

| File | Isi | Dihasilkan oleh |
|---|---|---|
| `online_retail_ii_clean.csv` | 1.007.913 baris transaksi bersih level baris (lihat aturan cleaning di README). **Tidak ikut di-push ke GitHub karena ukurannya 93,2 MB**; file ini tercantum di `.gitignore` dan dibuat ulang dengan `scripts/clean_data.py`. | `scripts/clean_data.py` |
| `cleaning_log.json` | Hitungan baris pada tiap langkah cleaning (mentah, duplikat, batal, quantity, price, hasil akhir). | `scripts/clean_data.py` |
| `monthly_sales.csv` | Agregat per bulan: revenue, orders, units, average order value. | `scripts/analyze.py` |
| `country_sales.csv` | Agregat per negara: revenue, orders, customers, units (43 negara). | `scripts/analyze.py` |
| `top_products.csv` | Top 10 produk (merchandise) by revenue. | `scripts/analyze.py` |
| `hourly_sales.csv` | Agregat per jam transaksi: orders dan revenue. | `scripts/analyze.py` |
| `weekday_sales.csv` | Agregat per hari dalam seminggu: orders dan revenue. | `scripts/analyze.py` |
| `SOURCES.md` | Dokumen ini. | manual |

## Catatan kualitas data mentah

- Invoice batal/retur memakai awalan huruf `C` pada nomor invoice.
- Sebagian baris berketerangan seperti `damages`, `lost`, `mixed`, `short` dengan
  Quantity negatif dan Price 0 adalah koreksi stok, bukan penjualan.
- Description untuk satu StockCode yang sama bisa tampil dengan beberapa varian
  ejaan/urutan kata di data mentah. Ranking produk karena itu dikunci pada
  StockCode; label Description di `top_products.csv` adalah varian yang paling
  sering muncul (modus) untuk kode tersebut.
- Tidak ada kolom cost, discount, atau promo di dataset ini. Konsekuensinya
  dibahas di README, bagian Keterbatasan.
