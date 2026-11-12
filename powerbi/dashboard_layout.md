# Layout Dashboard Power BI, 4 Halaman

Proyek: E-Commerce Sales Performance & Profitability
Sumber visual halaman 1: `dashboard_preview_halaman1.png` (dibuat dari data
asli, semua angkanya sama dengan `findings.json`).

Palet: marine `#14406B` untuk judul dan angka utama, biru muda `#2E6DA4`
untuk seri data, butter yellow `#F2C94C` hanya untuk aksen dan kotak catatan,
abu `#5D6D7E` untuk teks sekunder. Ukuran halaman 16:9.

## Halaman 1, Executive Sales Overview

- Judul halaman + keterangan periode (1 Des 2009 sampai 9 Des 2011).
- Slicer: dim_date[year_month], dim_country[country].
- 4 card measure: Total Revenue, Total Orders, Average Order Value,
  Basket Size.
- Line chart: sumbu dim_date[year_month], nilai Total Revenue. Beri
  anotasi "Nov 2011: £1.503.866,78" dan catatan Desember 2011 parsial.
- Kotak catatan: UK 85,03%, repeat customer 72,39%, karakter wholesale.

## Halaman 2, Product & Country Performance

- Bar chart horizontal: dim_product[description], nilai Total Revenue,
  top 10, filter is_merchandise = "Ya".
- Card: Top 10 Product Share (7,69%).
- Bar chart negara: dim_country[country], Total Revenue, top 6 termasuk UK.
- Card: UK Revenue Share (85,03%).
- Tabel 5 negara teratas di luar UK: EIRE, Netherlands, Germany, France,
  Australia, lengkap dengan orders dan customers agar kasus EIRE
  (revenue besar, hanya 5 customer) terlihat jelas.

## Halaman 3, Customer & Order Pattern

- Card: Total Customers (5.878), Repeat Customer Share (72,39%),
  Orders Tanpa Customer ID (3.108).
- Column chart: jumlah order per jam dari kolom `fact_sales[hour]`
  (jam puncak 12.00 dengan 6.427 order).
- Bar chart: order per weekday dari dim_date[weekday]
  (Thursday tertinggi 8.288 order, Saturday hanya 30 order).
- Kotak insight: pola jam kerja wholesale dan implikasi operasionalnya.

## Halaman 4, Data Quality & Profitability Notes

- Card: Revenue Tanpa Customer ID (£3.101.456,18) dan pangsa 15,15%.
- Ringkasan aturan cleaning Tahap 1: duplikat, invoice batal, quantity
  dan price tidak valid, dengan jumlah baris masing-masing dari
  `data/cleaning_log.json` di repo utama.
- Kotak batas analisis: tidak ada kolom cost sehingga margin tidak
  ditampilkan; ranking produk hanya merchandise; Desember 2011 parsial.
- Tabel verifikasi ringkas dari `measure_verification.csv`: measure,
  nilai fact, nilai findings, status COCOK.

## Aturan konsistensi

- Semua angka yang tampil sebagai teks statis harus disalin dari
  `findings.json`, bukan diketik dari ingatan.
- Format angka di card: pemisah ribuan titik dan desimal koma
  (gaya Indonesia), mata uang £ di depan.
