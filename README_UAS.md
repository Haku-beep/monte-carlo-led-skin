# Simulasi Monte Carlo Cahaya LED pada Kulit

Project UAS ini memperagakan transport paket foton pada satu lapisan kulit homogen. Program menghitung fraksi paket yang diserap, kembali keluar dari permukaan atas setelah hamburan, dan diteruskan menembus lapisan. Aplikasi web dibuat dengan Streamlit.

Model ini sengaja dibatasi agar alur Monte Carlo mudah dipahami. Ia belum mewakili semua detail masker LED atau jaringan kulit manusia.

## Menjalankan aplikasi

Pastikan Python sudah terpasang. Buka PowerShell di folder project, lalu jalankan:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit akan membuka alamat web lokal di peramban.

## Alur simulasi

1. Program meluncurkan paket foton tegak lurus ke lapisan kulit.
2. Jarak menuju tumbukan diambil secara acak dari `s = -ln(ξ) / μt`.
3. Pada tumbukan, foton diserap dengan peluang `μa / μt`; jika tidak, arahnya diubah dengan fungsi Henyey–Greenstein.
4. Proses berulang sampai foton diserap, keluar dari permukaan atas, keluar dari sisi bawah, atau mencapai batas langkah komputasi.
5. Hasil utama adalah fraksi `A`, `R`, dan `T`, serta jumlah foton terserap pada setiap interval kedalaman.

## Parameter awal

Contoh nilai awal diambil dari Girasol dkk. (2026) untuk kulit pada 660 nm:

- `μa = 0,03316 mm⁻¹`
- `μs′ = 1,88212 mm⁻¹`
- `g = 0,91`

Artikel melaporkan hamburan tereduksi `μs′`. Model satu lapis ini menggunakan koefisien hamburan biasa `μs` dalam persamaan jarak tumbukan, sehingga program menghitung `μs = μs′ / (1 − g)`. Satuan panjang harus konsisten; aplikasi memakai milimeter untuk ketebalan dan koefisien.

Nilai tersebut adalah nilai rata-rata sampel pada artikel, bukan nilai tetap untuk semua orang. Panjang gelombang pada model dikunci di 660 nm; mengubah panjang gelombang memerlukan data optik yang sesuai.

## Validasi

Aplikasi menjalankan pemeriksaan terpisah dengan `μs = 0`. Untuk berkas tegak lurus dan tanpa pantulan permukaan, transmisi Monte Carlo dibandingkan dengan hukum Beer–Lambert `T = exp(−μa d)`. Pemeriksaan ini menguji implementasi absorpsi pada kasus khusus tanpa hamburan; ia bukan perbandingan langsung untuk simulasi kulit yang memiliki hamburan.

Untuk simulasi utama, fraksi `A + R + T` mendekati satu jika semua paket sudah selesai. Jika sebagian kecil paket masih aktif saat batas langkah tercapai, aplikasi melaporkannya sebagai “belum selesai” secara terpisah.

## Asumsi dan batas penggunaan

- Satu lapisan homogen dengan permukaan bidang yang dianggap tidak berhingga.
- Sumber berupa berkas kolimasi yang datang tegak lurus.
- Paket foton memiliki bobot sama dan dapat terserap atau terhambur pada setiap tumbukan.
- Pantulan Fresnel, pembiasan, variasi lapisan kulit, dan sebaran sudut LED tidak dimodelkan.
- `R` berarti paket yang kembali keluar melalui sisi atas setelah hamburan; bukan pantulan Fresnel di permukaan.
- Grafik kedalaman menunjukkan fraksi paket awal yang terserap per interval. Grafik itu bukan peta fluens.
- Hasil hanya menjelaskan transport cahaya pada asumsi model, bukan SPF, keamanan, atau efektivitas klinis masker.

## Referensi parameter

Girasol, C. E., dkk. (2026). *Monte Carlo simulations of optical propagation in human skin using experimentally measured laser parameters*. **Lasers in Medical Science, 41**, 109. https://doi.org/10.1007/s10103-026-04911-7
