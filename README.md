# E-Commerce Sales Performance & Profitability

Analisis performa penjualan dan kualitas revenue sebuah perusahaan retail online
giftware berbasis di Inggris, periode **1 Desember 2009 sampai 9 Desember 2011**,
menggunakan dataset publik **Online Retail II** dari UCI Machine Learning
Repository (1.067.371 baris transaksi mentah).

> **Sumber data:** UCI Machine Learning Repository, dataset Online Retail II,
> diunduh langsung dari arsip resmi UCI pada 8 November 2026. Detail file,
> sitasi, dan lisensi ada di `data/SOURCES.md`.
>
> **Status:** Selesai, 3 dari 3 tahap. Tahap 1: data bersih, hitungan
> terverifikasi, query SQL, dan temuan awal. Tahap 2: notebook analisis lengkap
> (`analysis.ipynb`, 24 cell) dengan 12 chart. Tahap 3: kit Power BI
> (star schema + 13 measure DAX + panduan 4 halaman), deck presentasi
> 10 slide, dan modul belajar 5 halaman.
>
> **Catatan karakter bisnis:** menurut deskripsi resmi UCI, banyak customer
> perusahaan ini adalah wholesaler. Itu menjelaskan average order value dan
> basket size yang jauh lebih besar daripada e-commerce consumer biasa, dan
> angka di proyek ini harus dibaca sebagai penjualan wholesale giftware,
> bukan belanja ritel satuan.

## Pertanyaan bisnis

1. Berapa total revenue, jumlah order, dan jumlah customer selama dua tahun,
   dan bagaimana tren bulanannya?
2. Produk dan negara mana yang menyumbang revenue terbesar?
3. Seberapa besar nilai satu order pada umumnya (average order value dan
   basket size), dan seberapa terkonsentrasi revenue pada order besar?
4. Kapan pola transaksi paling ramai: bulan, hari, dan jam apa?
5. Berapa bagian customer yang kembali membeli (repeat purchase), dan berapa
   revenue yang tidak bisa diatribusikan ke customer mana pun?

## Definisi KPI

| KPI | Definisi di proyek ini |
|---|---|
| Revenue | `Quantity x Price` (GBP), hanya untuk transaksi non-batal yang valid menurut aturan cleaning di bawah. |
| Order | Satu nomor Invoice unik yang bukan invoice batal. |
| Customer teridentifikasi | Customer ID unik yang tidak kosong. Baris tanpa Customer ID tetap dihitung di revenue dan order, tetapi tidak masuk hitungan customer. |
| Average order value (AOV) | Total revenue dibagi jumlah order. Dilaporkan juga median nilai order. |
| Basket size | Jumlah unit (Quantity) per order; dilaporkan rata-rata dan median. |
| Repeat customer | Customer teridentifikasi dengan 2 order atau lebih. |

Catatan profitability: dataset ini **tidak memiliki kolom cost**, jadi gross
profit dan profit margin tidak dihitung dan tidak dikarang. Sisi profitability
yang diukur di proyek ini adalah kualitas revenue: AOV, basket size, konsentrasi
revenue pada order besar, repeat purchase, dan pangsa revenue per produk dan
negara.

## Cleaning

Semua langkah dijalankan oleh `scripts/clean_data.py`; hitungan per langkah
tersimpan di `data/cleaning_log.json`.

| Langkah | Baris dibuang | Alasan |
|---|---:|---|
| Baris mentah gabungan 2 sheet | 1.067.371 baris awal | |
| Duplikat persis (semua 8 kolom sama) | 34.335 | Baris yang sama tercatat dua kali; menyimpannya menggandakan revenue. |
| Invoice diawali `C` | 19.104 | Invoice batal/retur menurut dokumentasi dataset; bukan penjualan yang terealisasi. Sisa batal dari total 19.494 baris `C` mentah sudah terbuang sebagai duplikat. |
| Quantity <= 0 | 3.393 | Sisa baris negatif setelah invoice batal dibuang adalah koreksi stok berketerangan seperti damages, lost, dan mixed, bukan penjualan. |
| Price <= 0 | 2.626 | Harga nol atau negatif bukan transaksi penjualan yang valid. |
| **Hasil akhir (data bersih)** | **1.007.913 baris** | |

Keputusan yang disengaja:

- **Customer ID kosong dipertahankan** (228.488 baris bersih). Transaksinya
  penjualan nyata; membuangnya akan menghapus revenue sebesar GBP 3.101.456,18
  (15,15% dari total) dan mengecilkan gambaran penjualan. Baris ini hanya
  dikeluarkan dari analisis per customer.
- **Description kosong tidak ada yang tersisa** di data bersih: seluruh baris
  tanpa Description ternyata berada di kelompok koreksi yang sudah dibuang.
- **Ranking produk hanya memakai StockCode berawalan digit.** Kode berawalan
  huruf (POST, DOT, M, BANK CHARGES, AMAZONFEE, gift voucher, dan sejenisnya)
  adalah ongkir, penyesuaian manual, atau voucher, bukan merchandise.

## Temuan kunci

Seluruh angka di bawah dihitung dari data bersih dan **diverifikasi dua cara
independen** (pandas dan SQL lewat SQLite, hasil 12 dari 12 cocok; lihat bagian
Verifikasi). Angka lengkap ada di `findings.json`.

- **Total revenue GBP 20.476.260,43** dari **40.077 order** dan **11.205.148 unit**
  terjual, dilayani untuk **5.878 customer teridentifikasi** di 43 negara.
- **Nilai order besar dan khas wholesale:** average order value GBP 510,92
  (median GBP 302,22) dan basket size rata-rata 279,59 unit per order
  (median 146 unit).
- **November adalah puncak di kedua tahun:** November 2011 menjadi bulan
  terbaik dengan revenue GBP 1.503.866,78 dari 2.769 order, dan November 2010
  hampir sama tinggi (GBP 1.464.293,14). Polanya konsisten dengan lonjakan
  pre-Christmas untuk giftware. Desember 2011 tidak bisa dibandingkan sebagai
  bulan penuh karena data berakhir 9 Desember 2011.
- **Satu order terbesar bernilai GBP 168.469,60** (invoice 581483, 9 Desember
  2011, 80.995 unit produk PAPER CRAFT , LITTLE BIRDIE). Hanya 93 order yang
  bernilai di atas GBP 10.000, tetapi kelompok kecil itu menyumbang 8,87%
  revenue, jadi revenue cukup sensitif terhadap sedikit order wholesale besar.
- **United Kingdom mendominasi** dengan 85,03% revenue. Di luar UK, penyumbang
  terbesar adalah EIRE (GBP 658.767,31, tetapi hanya dari 5 customer),
  Netherlands (GBP 554.038,09), Germany (GBP 425.019,71), France
  (GBP 350.456,09), dan Australia (GBP 169.283,46).
- **Produk terlaris by revenue adalah REGENCY CAKESTAND 3 TIER**
  (GBP 330.590,32), disusul WHITE HANGING HEART T-LIGHT HOLDER
  (GBP 257.724,71) dan JUMBO BAG RED RETROSPOT (GBP 180.569,34). Top 10 produk
  hanya menyumbang 7,69% revenue, artinya revenue tersebar di banyak produk
  dan tidak bergantung pada sedikit produk unggulan.
- **Repeat purchase kuat:** 72,39% customer teridentifikasi membeli 2 kali
  atau lebih, dengan median 3 order per customer.
- **Pola waktu sangat mengikuti jam kerja:** order terbanyak terjadi pukul
  12.00 (6.427 order), dan hampir semua aktivitas berada di rentang pukul
  08.00 sampai 17.00. Hari tersibuk adalah Thursday (8.288 order,
  GBP 4.195.212,76). Saturday hampir tidak ada transaksi (30 order,
  GBP 9.803,05), sementara Sunday justru ramai (4.835 order).
- **15,15% revenue tidak teratribusi:** revenue sebesar GBP 3.101.456,18 dari
  3.108 order tidak memiliki Customer ID, sehingga analisis customer hanya
  mencakup sekitar 85% revenue.

## Verifikasi angka

- Cara 1: agregasi pandas di `scripts/analyze.py`, hasilnya `findings.json`
  dan CSV agregat di `data/`.
- Cara 2: hitung ulang dengan SQL murni lewat SQLite in-memory di
  `scripts/verify_sqlite.py` (database in-memory, tidak ada file .db di repo).
  Hasil terakhir: **12 dari 12 pemeriksaan cocok** (total revenue, orders,
  customers, units, AOV, basket size, rentang tanggal, bulan terbaik, top 10
  produk, negara teratas di luar UK, jam puncak).
- `sql/queries.sql` berisi 12 query sales performance dan sudah dijalankan
  terhadap tabel `sales_clean` hasil `scripts/load_to_sqlite.py` tanpa error.
- Kit Power BI Tahap 3: 11 dari 11 measure di `powerbi/measure_verification.csv`
  dihitung ulang dari `fact_sales` dan cocok persis dengan `findings.json`
  (selisih 0).

Cara reproduksi:

```bash
pip install -r requirements.txt
# unduh online_retail_ii.zip dari tautan di data/SOURCES.md, ekstrak xlsx-nya
# ke luar repo (default yang dicari script: ~/workspace/ecommerce-raw/)
python scripts/clean_data.py
python scripts/analyze.py
python scripts/verify_sqlite.py
python scripts/load_to_sqlite.py /tmp/ecommerce_sales.db
sqlite3 /tmp/ecommerce_sales.db < sql/queries.sql
```

## Dashboard Power BI (Tahap 3)

Star schema: `fact_sales` (grain satu baris transaksi bersih) dengan
`dim_product` (StockCode, Description modus), `dim_customer`, `dim_country`,
dan `dim_date` (tanggal, bulan, hari, jam). File `fact_sales` dipecah per tahun
(`fact_sales_2009.csv`, `fact_sales_2010.csv`, `fact_sales_2011.csv`) supaya
tiap file tetap ringan; total 996.548 baris dan revenue GBP 20.476.260,43,
cocok dengan data bersih. Rakit dashboard mengikuti `powerbi/build_guide.md`
dan `powerbi/dashboard_layout.md`; 13 measure DAX ada di
`powerbi/measures_dax.md`.

1. **Halaman 1, Executive Sales Overview:** card total revenue, orders, AOV,
   basket size, dan customers; tren revenue bulanan; peringatan visual bahwa
   Desember 2011 adalah bulan parsial.
2. **Halaman 2, Product & Country Performance:** top 10 produk by revenue,
   pangsa UK vs internasional, top 5 negara di luar UK, dan konsentrasi
   top 10 produk (7,69%).
3. **Halaman 3, Customer & Order Pattern:** repeat purchase, distribusi nilai
   order, pola jam dan hari, serta order besar di atas GBP 10.000.
4. **Halaman 4, Data Quality & Profitability Notes:** revenue tanpa Customer ID
   (15,15%), catatan tidak adanya cost sehingga margin tidak ditampilkan,
   dan ringkasan aturan cleaning.

## Struktur repo

```
├── README.md                  # dokumen ini
├── findings.json              # angka kunci terverifikasi dua cara
├── requirements.txt
├── analysis.ipynb             # notebook analisis lengkap, 24 cell (Tahap 2)
├── Portofolio-Ecommerce-Sales-Performance.pptx  # deck 10 slide (Tahap 3)
├── Modul-Ecommerce-Sales-Performance.pdf        # modul belajar 5 halaman (Tahap 3)
├── data/
│   ├── SOURCES.md             # sumber resmi, sitasi, lisensi, daftar file
│   ├── cleaning_log.json      # hitungan baris per langkah cleaning
│   ├── monthly_sales.csv      # agregat bulanan
│   ├── country_sales.csv      # agregat per negara
│   ├── top_products.csv       # top 10 produk by revenue
│   ├── hourly_sales.csv       # agregat per jam
│   ├── weekday_sales.csv      # agregat per hari
│   └── customer_repeat_summary.csv  # ringkasan repeat purchase (Tahap 2)
│       (online_retail_ii_clean.csv dibuat lokal oleh clean_data.py,
│        tidak di-push karena 93,2 MB - lihat .gitignore)
├── charts/                    # 12 chart Tahap 2
│   ├── 01_monthly_revenue_trend.png
│   ├── 02_seasonal_revenue_by_month_year.png
│   ├── 03_top10_products.png
│   ├── 04_top_countries_non_uk.png
│   ├── 05_hourly_pattern.png
│   ├── 06_weekday_pattern.png
│   ├── 07_order_value_distribution.png
│   ├── 08_aov_by_month.png
│   ├── 09_uk_vs_nonuk_share.png
│   ├── 10_large_order_concentration.png
│   ├── 11_repeat_vs_onetime.png
│   └── 12_heatmap_month_year.png
├── powerbi/                   # kit Power BI Tahap 3
│   ├── build_guide.md         # langkah rakit dashboard di Power BI Desktop
│   ├── dashboard_layout.md    # layout 4 halaman
│   ├── dashboard_preview_halaman1.png
│   ├── dim_country.csv        # 43 negara
│   ├── dim_customer.csv       # 5.878 customer + sentinel 0
│   ├── dim_date.csv           # 604 tanggal transaksi
│   ├── dim_product.csv        # 4.917 produk
│   ├── fact_sales_2009.csv    # 42.989 baris
│   ├── fact_sales_2010.csv    # 474.483 baris
│   ├── fact_sales_2011.csv    # 479.076 baris
│   ├── measure_verification.csv  # 11 measure terverifikasi cocok
│   └── measures_dax.md        # 13 measure DAX
├── scripts/
│   ├── clean_data.py          # unduhan mentah -> data bersih + cleaning log
│   ├── analyze.py             # agregasi pandas -> findings.json + CSV agregat
│   ├── load_to_sqlite.py      # data bersih -> tabel sales_clean (db di luar repo)
│   ├── verify_sqlite.py       # verifikasi independen cara 2 (SQL/SQLite)
│   ├── build_charts.py        # membangun 12 chart Tahap 2
│   ├── make_notebook.py       # membangun analysis.ipynb (Tahap 2)
│   └── build_stage3.py        # membangun ulang kit Power BI Tahap 3
└── sql/
    └── queries.sql            # 12 query sales performance
```

## Keterbatasan

- Desember 2011 hanya berisi data sampai 9 Desember, jadi perbandingan bulan
  penuh untuk bulan itu tidak valid; AOV Desember 2011 yang tinggi (GBP 778,76)
  ikut terangkat oleh order terbesar di dataset yang terjadi pada 9 Desember.
- Tidak ada kolom cost, discount, dan promo, sehingga profit margin dan
  efektivitas promo tidak bisa dianalisis dari dataset ini.
- Karakter wholesale membuat AOV dan basket size tidak bisa dibandingkan
  langsung dengan e-commerce consumer.
- 15,15% revenue tanpa Customer ID membatasi cakupan analisis customer.
- Description memiliki beberapa varian ejaan untuk StockCode yang sama;
  analisis produk dikunci pada StockCode.
- Dashboard Power BI belum pernah dibuka di Power BI Desktop (dibangun dan
  diverifikasi numerik di Linux). Pembukaan pertama mengikuti Langkah 4
  `powerbi/build_guide.md`.
