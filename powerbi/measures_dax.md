# Measure DAX, Kit Power BI E-Commerce Sales Performance & Profitability

Semua measure ditulis dengan nama polos dan hanya membaca `fact_sales`
(grain: 1 baris = 1 invoice x 1 produk, 996.548 baris) beserta relasi ke
`dim_product`, `dim_customer`, `dim_country`, dan `dim_date`.
Setiap measure sudah dihitung ulang dari fact_sales dan dibandingkan dengan
`findings.json` Tahap 1 di `measure_verification.csv`: semua cocok, selisih 0.

## Measure inti

```dax
Total Revenue =
SUM ( fact_sales[revenue_gbp] )
-- Hasil tanpa filter: £20.476.260,43
```

```dax
Total Orders =
DISTINCTCOUNT ( fact_sales[invoice] )
-- Hasil tanpa filter: 40.077
```

```dax
Total Units =
SUM ( fact_sales[quantity] )
-- Hasil tanpa filter: 11.205.148
```

```dax
Total Customers =
CALCULATE (
    DISTINCTCOUNT ( fact_sales[customer_id] ),
    fact_sales[customer_id] <> 0
)
-- Customer 0 adalah sentinel "tidak teridentifikasi" dan tidak dihitung.
-- Hasil tanpa filter: 5.878
```

## Measure turunan

```dax
Average Order Value =
DIVIDE ( [Total Revenue], [Total Orders] )
-- Hasil tanpa filter: £510,92
```

```dax
Basket Size =
DIVIDE ( [Total Units], [Total Orders] )
-- Hasil tanpa filter: 279,59 unit per order
```

```dax
UK Revenue =
CALCULATE ( [Total Revenue], dim_country[is_uk] = "Ya" )
-- Hasil tanpa filter: £17.410.196,10
```

```dax
UK Revenue Share =
DIVIDE ( [UK Revenue], [Total Revenue] )
-- Format persen, 2 desimal. Hasil tanpa filter: 85,03%
```

```dax
Revenue Tanpa Customer ID =
CALCULATE ( [Total Revenue], dim_customer[is_identified] = "Tidak" )
-- Hasil tanpa filter: £3.101.456,18 (15,15% dari Total Revenue)
```

```dax
Orders Tanpa Customer ID =
CALCULATE ( [Total Orders], dim_customer[is_identified] = "Tidak" )
-- Hasil tanpa filter: 3.108
```

```dax
Repeat Customers =
CALCULATE (
    COUNTROWS ( dim_customer ),
    FILTER (
        dim_customer,
        dim_customer[customer_id] <> 0
            && CALCULATE ( [Total Orders] ) >= 2
    )
)
-- Hasil tanpa filter: 4.255
```

```dax
Repeat Customer Share =
DIVIDE ( [Repeat Customers], [Total Customers] )
-- Format persen, 2 desimal. Hasil tanpa filter: 72,39%
```

```dax
Top 10 Product Share =
VAR Top10Revenue =
    SUMX (
        TOPN ( 10, VALUES ( dim_product[stock_code] ), [Total Revenue], DESC ),
        [Total Revenue]
    )
RETURN
    DIVIDE ( Top10Revenue, [Total Revenue] )
-- Catatan: pakai measure ini bersama filter is_merchandise = "Ya" di halaman
-- produk agar kode ongkir (POST, BANK CHARGES, dan sejenisnya) tidak ikut
-- ranking. Hasil dengan filter merchandise: 7,69%
```

## Catatan grain dan batas measure

- fact_sales sudah diagregasi per invoice x produk, jadi SUM dan
  DISTINCTCOUNT invoice tetap menghasilkan angka Tahap 1 yang persis sama.
- Tidak ada measure profit atau margin di kit ini. Dataset tidak memiliki
  kolom cost; menambahkannya berarti mengarang angka.
- Desember 2011 adalah bulan parsial (data berakhir 9 Des 2011). Jangan
  buat measure perbandingan bulan penuh untuk bulan itu tanpa catatan.
