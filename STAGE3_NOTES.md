# Catatan Staging Tahap 3, E-Commerce Sales Performance & Profitability

Folder ini adalah STAGING Tahap 3. Isinya belum masuk repo utama supaya
jumlah file push Hari 1 dan Hari 2 tidak berubah. Pada Hari 3, isinya
dipindah ke repo `ecommerce-sales-profitability-analysis` dengan struktur
yang sama (folder `powerbi/`, `charts/`, `scripts/`, dan dua file
deliverable di root repo).

## Isi (16 file)

Kit Power BI, folder `powerbi/` (10 file):

- `fact_sales.csv`: star schema, grain 1 baris = 1 invoice x 1 produk,
  996.548 baris, sekitar 54 MB. Kolom: invoice, stock_code, customer_id,
  country, invoice_date, hour, quantity, revenue_gbp.
- `dim_product.csv` (4.917 produk), `dim_customer.csv` (5.878 customer +
  sentinel 0 tidak teridentifikasi), `dim_country.csv` (43 negara),
  `dim_date.csv` (604 tanggal yang memiliki transaksi).
- `measures_dax.md`: 13 measure bernama polos.
- `measure_verification.csv`: 11 measure dihitung dari fact_sales dan
  dibandingkan dengan findings.json Tahap 1, semua COCOK dengan selisih 0,
  plus 1 baris info grain.
- `dashboard_layout.md`: layout 4 halaman sesuai rencana di README.
- `build_guide.md`: langkah rakit Power BI Desktop, termasuk langkah
  verifikasi sebelum membuat visual.
- `dashboard_preview_halaman1.png`: preview halaman 1 dari data asli,
  angka di gambar sama dengan findings.

Chart untuk deck dan modul, folder `charts/` (2 file):
`monthly_revenue_trend.png`, `top10_products_revenue.png`.

Script (1 file): `scripts/build_stage3.py`, membangun ulang semua output
di folder ini dari data bersih repo utama dan findings.json.

Deliverable root staging (2 file):

- `Portofolio-Ecommerce-Sales-Performance.pptx`: 10 slide, 16:9.
- `Modul-Ecommerce-Sales-Performance.pdf`: modul belajar 5 halaman A4,
  6 bab + latihan + glosarium.

Catatan ini (1 file): `STAGE3_NOTES.md`.

## Keputusan PBIP

Paket PBIP TIDAK dibuat di tahap ini. Pada proyek sebelumnya (Inflasi)
paket PBIP berisi sekitar 70 file; memasukkannya akan membuat Tahap 3
meledak jauh di atas target 16 sampai 20 file. PBIP dicatat sebagai
opsional terpisah dan bisa dibuat belakangan sebagai push tambahan tanpa
mengubah isi kit, PPT, dan modul. Tidak ada file .pbix di staging ini:
dashboard resmi dirakit manual dari kit mengikuti build guide, sama
seperti pola proyek sebelumnya.

## Keterbatasan

- fact_sales berukuran sekitar 54 MB. Masih di bawah batas file GitHub
  100 MB, tetapi ini file terbesar di repo. Grain invoice x produk adalah
  yang paling ringkas yang tetap mempertahankan DISTINCTCOUNT order dan
  semua measure secara persis.
- Dashboard belum pernah dibuka di Power BI Desktop (lingkungan ini
  Linux tanpa Power BI Desktop). Verifikasi yang dilakukan bersifat
  numerik: measure dihitung ulang dari fact_sales di luar Power BI dan
  cocok persis dengan findings. Pembukaan pertama di Power BI Desktop
  tetap perlu dilakukan mengikuti Langkah 4 build guide.
- Pola jam memakai kolom `hour` di fact_sales (jam invoice), karena
  dim_date grainnya tanggal.
