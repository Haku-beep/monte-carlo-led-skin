# Monte Carlo LED pada Kulit

Simulasi interaktif sederhana untuk project UAS Metode Monte Carlo. Paket foton bergerak di dalam satu lapisan kulit homogen pada panjang gelombang 660 nm. Perhitungan berjalan di peramban dengan JavaScript; tidak memerlukan Python, server, atau alat eksperimen.

## Isi folder

- `index.html` — susunan halaman dan kontrol simulasi.
- `style.css` — tampilan halaman.
- `app.js` — algoritma Monte Carlo dan grafik.

## Cara mencoba

Buka `index.html` di peramban, ubah parameter, lalu pilih **Jalankan simulasi**. Untuk menerbitkannya lewat GitHub Pages, unggah ketiga berkas tersebut bersama README ini ke repositori GitHub. Pastikan `index.html` berada di direktori utama repositori. Di pengaturan repositori, buka **Settings → Pages**, pilih publikasi dari branch `main` dan direktori `/ (root)`, lalu simpan. GitHub akan menyediakan tautan situs setelah publikasi selesai.

Panduan resmi: [Membuat situs GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Alur Monte Carlo

1. Paket foton dimulai di permukaan dan bergerak tegak lurus ke dalam lapisan.
2. Jarak menuju tumbukan diambil dari `s = -ln(ξ) / μt`.
3. Pada tumbukan, paket diserap dengan peluang `μa / μt`. Jika tidak terserap, arah hamburannya diambil dari fungsi Henyey–Greenstein.
4. Gerak berlanjut sampai paket terserap, keluar dari permukaan atas, keluar dari sisi bawah, atau mencapai batas langkah komputasi.

Program melaporkan fraksi `A` (diserap), `R` (keluar kembali dari atas setelah hamburan), dan `T` (diteruskan ke bawah). Grafik kedalaman menunjukkan bagian dari seluruh paket awal yang diserap pada tiap interval kedalaman; grafik itu bukan peta fluens.

## Nilai awal dan satuan

Nilai optik awal diambil dari Girasol dkk. (2026) untuk sampel kulit pada 660 nm:

- `μa = 0,03316 mm⁻¹`
- `μs′ = 1,88212 mm⁻¹`
- `g = 0,91`

`μs′` adalah koefisien hamburan tereduksi. Untuk mengambil jarak antarinteraksi, kode mengubahnya menjadi koefisien hamburan biasa dengan `μs = μs′ / (1 − g)`. Ketebalan dan koefisien memakai satuan mm dan mm⁻¹.

Referensi: Girasol, C. E., dkk. (2026). *Monte Carlo simulations of optical propagation in human skin using experimentally measured laser parameters*. **Lasers in Medical Science, 41**, 109. https://doi.org/10.1007/s10103-026-04911-7

Nilai artikel adalah hasil pengukuran sampel dan bukan nilai universal untuk semua orang. Sumber yang dibahas artikel tersebut berupa laser; model ini memakai nilai optik jaringannya, tetapi tidak meniru bentuk pancaran masker LED.

## Validasi

Simulasi kedua meniadakan hamburan (`μs = 0`). Untuk berkas tegak lurus dan tanpa pantulan permukaan, transmisinya dibandingkan dengan Beer–Lambert, `T = exp(−μa d)`. Ini pemeriksaan khusus untuk absorpsi murni, bukan pembanding setara bagi model jaringan yang mengalami hamburan.

## Asumsi dan batas model

- Kulit dimodelkan sebagai satu lapisan homogen dengan permukaan datar dan tak berhingga.
- Paket foton memiliki bobot sama. Pada setiap tumbukan, paket diserap atau dihamburkan.
- Pantulan Fresnel, pembiasan, beberapa lapisan kulit, posisi LED, dan sudut pancaran LED belum dimodelkan.
- `R` hanya menghitung paket yang kembali keluar karena hamburan, bukan pantulan Fresnel di permukaan.
- Model menjelaskan transport cahaya pada asumsi tersebut; hasilnya tidak menunjukkan SPF, keamanan, atau efektivitas klinis masker.
