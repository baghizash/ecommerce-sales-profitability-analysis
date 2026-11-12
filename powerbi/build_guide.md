# Build Guide Power BI Desktop, E-Commerce Sales Performance & Profitability

Panduan langkah demi langkah untuk merakit dashboard dari kit di folder
`powerbi/` ini. Waktu rakit perkiraan 45 sampai 60 menit.

## Yang disiapkan

- Power BI Desktop (versi terbaru) di Windows.
- Folder kit ini berisi: `fact_sales.csv`, `dim_product.csv`,
  `dim_customer.csv`, `dim_country.csv`, `dim_date.csv`,
  `measures_dax.md`, `measure_verification.csv`,
  `dashboard_layout.md`, dan `dashboard_preview_halaman1.png`.

## Langkah 1, ambil data

1. Buka Power BI Desktop, pilih Get Data, Text/CSV.
2. Muat kelima file CSV satu per satu. `fact_sales.csv` berukuran sekitar
   49 MB dengan 996.548 baris, tunggu sampai selesai dimuat.
3. Di Power Query, periksa tipe kolom: `invoice` dan `stock_code` sebagai
   Text, `customer_id` sebagai Whole Number, `invoice_date` dan `date`
   sebagai Date, `quantity` sebagai Whole Number, `revenue_gbp` sebagai
   Decimal Number. Ini penting: invoice dan stock code yang terbaca
   sebagai angka akan menghilangkan angka nol di depan dan merusak relasi.

## Langkah 2, buat relasi star schema

Di tampilan Model, buat relasi satu ke banyak (dimensi ke fact):

- `dim_product[stock_code]` ke `fact_sales[stock_code]`
- `dim_customer[customer_id]` ke `fact_sales[customer_id]`
- `dim_country[country]` ke `fact_sales[country]`
- `dim_date[date]` ke `fact_sales[invoice_date]`

Semua relasi satu arah dari dimensi ke fact. Setelah itu sembunyikan
kolom kunci di sisi fact dari tampilan Report.

## Langkah 3, buat measure

1. Buat tabel kosong khusus bernama `Measures` (Enter Data, satu kolom
   dummy, lalu hapus kolomnya setelah measure pertama dibuat).
2. Salin satu per satu rumus dari `measures_dax.md` sebagai measure baru.
3. Atur format: Total Revenue, Average Order Value, UK Revenue, dan
   Revenue Tanpa Customer ID sebagai Currency £ dengan 2 desimal;
   UK Revenue Share, Repeat Customer Share, dan Top 10 Product Share
   sebagai Percentage dengan 2 desimal; Basket Size sebagai Decimal
   dengan 2 desimal.

## Langkah 4, verifikasi sebelum membuat visual apa pun

1. Buat satu halaman sementara, letakkan card untuk setiap measure inti.
2. Bandingkan dengan `measure_verification.csv`. Nilai yang harus muncul
   persis: Total Revenue £20.476.260,43; Total Orders 40.077;
   Average Order Value £510,92; Total Units 11.205.148; Basket Size
   279,59; Total Customers 5.878; UK Revenue Share 85,03%;
   Revenue Tanpa Customer ID £3.101.456,18.
3. Kalau ada yang berbeda, periksa dulu tipe kolom dan relasi di
   Langkah 1 dan 2. Jangan lanjut ke layout sebelum semua cocok.

## Langkah 5, rakit 4 halaman

Ikuti `dashboard_layout.md` halaman demi halaman. Halaman 1 dapat
dibandingkan langsung dengan `dashboard_preview_halaman1.png`: susunan
card, tren bulanan, dan kotak catatannya harus serupa, termasuk anotasi
puncak November 2011 dan catatan Desember 2011 parsial.

## Langkah 6, simpan

Simpan sebagai file `.pbix` dengan nama
`Ecommerce-Sales-Performance.pbix` di luar folder kit, misalnya di folder
proyek utama. File `.pbix` hasil rakitan manual inilah file dashboard
resminya; kit ini memang tidak menyertakan `.pbix` bawaan.
