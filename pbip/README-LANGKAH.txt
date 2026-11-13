PAKET POWER BI PROJECT (.pbip) — E-Commerce Sales Performance & Profitability
==============================================================================

Isi paket ini adalah project Power BI (format .pbip) yang sudah dirakit:
model data (5 tabel), 13 measure DAX, 4 relasi, dan 4 halaman dashboard
sesuai panduan kit proyek ecommerce-sales-profitability-analysis (Tahap 3).
Tinggal dibuka, diarahkan ke folder data, refresh, lalu simpan sebagai .pbix.

Dataset: UCI Online Retail II (1 Des 2009 – 9 Des 2011), grain fact
1 baris = 1 invoice x 1 produk, 996.548 baris. Fact dimuat dari 3 file
per tahun (fact_sales_2009.csv, fact_sales_2010.csv, fact_sales_2011.csv)
yang digabung otomatis di Power Query — file gabungan 52 MB tidak dipakai.

LANGKAH MEMBUKA
---------------
1. Extract paket ini di mana saja (misalnya D:\PowerBI\EcommerceSales\).
2. Buka file EcommerceSales.pbip dengan Power BI Desktop.
3. Kalau data gagal dimuat (error FolderData): menu Modeling → Edit parameters
   → isi FolderData dengan path folder "data" hasil extract
   (contoh: D:\PowerBI\EcommerceSales\data) → OK → Refresh.
   Default parameter adalah C:\PowerBI\EcommerceSales\data.
4. Setelah semua tabel termuat, File → Save As → simpan sebagai .pbix.
5. Cek cepat di halaman Executive Sales Overview (tanpa menyentuh slicer):
   - Total Revenue harus £20.476.260,43
   - Total Orders harus 40.077
   - Average Order Value harus £510,92
   - Basket Size harus 279,59
   - Halaman 2: UK Revenue Share 85,03%; Top 10 Product Share 7,69%
   - Halaman 3: Total Customers 5.878; Repeat Customer Share 72,39%

CATATAN / HAL YANG MUNGKIN PERLU SENTUHAN KECIL SAAT PERTAMA DIBUKA
--------------------------------------------------------------------
- Kolom invoice di model bertipe TEKS, bukan angka. Itu disengaja: ada 1 baris
  invoice penyesuaian "A563185"; kalau invoice dipaksa jadi angka, baris itu
  gagal dimuat dan Total Orders berubah dari 40.077.
- Bar produk halaman 2 difilter is_merchandise = "Ya" dan diurutkan dari
  revenue terbesar, tetapi tidak dikunci ke tepat 10 baris (filter TopN tidak
  dipasang di file definisi). Kalau mau persis 10 produk: pilih visual →
  panel Filters → description → Filter type "Top N" → Show items Top 10
  by Total Revenue. Measure Top 10 Product Share sendiri sudah menghitung
  tepat 10 produk (7,69%).
- Tabel negara di luar UK halaman 2 menampilkan semua negara non-UK urut
  revenue terbesar (bukan dikunci 5 baris), supaya urutan EIRE, Netherlands,
  Germany, France, Australia terlihat lengkap.
- Tabel verifikasi measure di panduan layout halaman 4 ditampilkan sebagai
  kotak teks ringkasan (11 dari 11 angka COCOK, selisih 0), karena
  measure_verification.csv bukan bagian model data; file aslinya ada di kit
  Tahap 3 kalau perlu dilihat baris per baris.
- Judul dan ukuran font visual memakai format bawaan tema; warna mengikuti
  palet kit (marine #14406B, biru #2E6DA4, butter yellow #F2C94C).

KEJUJURAN VALIDASI
------------------
Paket ini divalidasi secara STRUKTURAL saja (skrip validate_pbip.py: semua
JSON dan TMDL ter-parse, semua referensi visual menunjuk kolom/measure yang
ada, semua CSV yang dirujuk tersedia). Paket ini BELUM PERNAH dibuka di
Power BI Desktop (tidak bisa dijalankan di mesin Linux tempat paket dirakit),
jadi pemeriksaan pertama saat dibuka di Power BI Desktop adalah uji
sebenarnya. Kalau ada error, kirim screenshot-nya untuk diperbaiki.

SUMBER DATA: kit Power BI proyek ecommerce-sales-profitability-analysis
(Tahap 3), dataset UCI Online Retail II (DOI 10.24432/C5CG6D, CC BY 4.0).
Folder data/ berisi 4 CSV dimensi yang sama dengan kit + 3 CSV fact per tahun.
