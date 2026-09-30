# AntiBot Fetch

**Ambil data dari situs yang dilindungi Cloudflare, Akamai, atau DataDome — tanpa browser, tanpa Selenium, tanpa captcha solver.**

Program Python ringan yang membuat script Anda terlihat seperti browser sungguhan di mata sistem keamanan website.

```python
from antibot import fetch

r = fetch("https://target.com")
print(r.status_code, len(r.text))
```

Selesai. Tidak ada konfigurasi rumit.

---

## Daftar Isi

- [Apa itu program ini?](#apa-itu-program-ini)
- [Kenapa situs memblokir script Anda?](#kenapa-situs-memblokir-script-anda)
- [Persiapan](#persiapan)
- [Cara Pakai — Panduan Pemula](#cara-pakai--panduan-pemula)
- [Cara Pakai — Mode Lanjutan](#cara-pakai--mode-lanjutan)
- [Daftar Browser yang Didukung](#daftar-browser-yang-didukung)
- [Apa yang Bisa dan Tidak Bisa Dilakukan](#apa-yang-bisa-dan-tidak-bisa-dilakukan)
- [Pertanyaan yang Sering Ditanyakan](#pertanyaan-yang-sering-ditanyakan)
- [Cara Kerja (versi teknis)](#cara-kerja-versi-teknis)
- [Pemecahan Masalah](#pemecahan-masalah)

---

## Apa itu program ini?

Pernah membuat script Python sederhana untuk mengambil data dari sebuah website, lalu tiba-tiba dapat balasan **403 Forbidden** padahal di browser biasa situs itu terbuka normal?

Itu bukan karena script Anda salah. Itu karena website mendeteksi bahwa koneksi Anda **bukan dari browser sungguhan**.

Program ini menyelesaikan masalah itu. Ia membuat koneksi dari script Python Anda **identik dengan koneksi browser asli** — bukan hanya soal nama browser yang dipalsukan, tapi sampai lapisan keamanan jaringan di bawahnya.

**Singkatnya:** script Anda jadi tidak bisa dibedakan dari orang yang membuka situs itu pakai Chrome.

---

## Kenapa situs memblokir script Anda?

Setiap kali browser (atau script) terhubung ke sebuah website, ia mengirim "ciri-ciri" di balik layar. Sistem keamanan website membaca ciri-ciri itu untuk menilai: **ini manusia atau robot?**

Ada tiga lapisan yang diperiksa:

| Lapisan | Apa yang dilihat website | `requests` biasa | Program ini |
|---|---|---|---|
| **TLS** (jabat tangan awal) | Sidik jari algoritma enkripsi | Mencurigakan | Sama seperti Chrome |
| **HTTP/2** | Pola komunikasi tingkat lanjut | Mencurigakan | Sama seperti Chrome |
| **Header** | Susunan & kelengkapan informasi | Kurang lengkap | Sama seperti Chrome |

Mengganti nama browser (`User-Agent`) saja **tidak cukup** — website masih bisa melihat dua lapisan pertama dan langsung tahu itu robot. Program ini memperbaiki ketiganya sekaligus.

---

## Persiapan

### Langkah 1 — Pasang Python

Buka <https://www.python.org/downloads/>, unduh, jalankan. ⚠️ **Centang "Add Python to PATH"** di layar pertama.

### Langkah 2 — Pasang pustaka

Buka Command Prompt / Terminal:

```
pip install curl_cffi
```

Hanya satu pustaka. Itu saja.

### Langkah 3 — Unduh program ini

- **Tanpa Git:** klik tombol hijau **Code** di halaman ini → **Download ZIP** → ekstrak
- **Dengan Git:** `git clone https://github.com/ahmadghozali-xyz/antibot-fetch.git`

### Langkah 4 — Uji

Masuk ke folder program, lalu jalankan:

```
python antibot.py
```

Kalau muncul `selftest OK — profil: ...`, program siap dipakai.

---

## Cara Pakai — Panduan Pemula

### Contoh 1: Ambil satu halaman

Buat file `coba.py`:

```python
from antibot import fetch

r = fetch("https://target.com")
print(r.status_code)
print(r.text[:500])
```

Jalankan:

```
python coba.py
```

Kalau `status_code` = 200, berhasil.

### Contoh 2: Situs yang butuh cookie (login, atau melewati pemeriksaan)

Beberapa situs memberi Anda "tiket masuk" (cookie) setelah kunjungan pertama. Tiket itu harus dibawa saat mengakses halaman berikutnya — sama seperti browser.

```python
from antibot import Session

with Session("chrome131") as s:
    s.get("https://target.com")              # kunjungan pertama, ambil tiket
    print(s.cookies_dict())                  # lihat tiket yang didapat

    r = s.get("https://target.com/halaman")  # kunjungan berikutnya
    print(r.status_code)
```

Kata kunci `with` memastikan koneksi ditutup rapi setelah selesai.

### Contoh 3: Kirim data (form / API)

```python
from antibot import Session

with Session("chrome131") as s:
    r = s.post("https://target.com/api", json={"kata": "kunci"})
    print(r.json())
```

### Contoh 4: Ganti browser

```python
from antibot import fetch

r = fetch("https://target.com", profile="firefox133")
```

---

## Cara Pakai — Mode Lanjutan

### Fungsi `fetch()` — sekali jalan

```python
fetch(url, profile="chrome", method="GET", headers=None, retries=2, retry_wait=1.5, **kwargs)
```

| Parameter | Default | Keterangan |
|---|---|---|
| `url` | — | Alamat tujuan |
| `profile` | `"chrome"` | Browser yang ditiru |
| `method` | `"GET"` | `GET`, `POST`, `PUT`, `DELETE`, dll. |
| `headers` | `None` | Header tambahan Anda |
| `retries` | `2` | Berapa kali coba ulang kalau koneksi putus |
| `retry_wait` | `1.5` | Jeda antar percobaan (detik) |
| `**kwargs` | — | Diteruskan ke pustaka (`json=`, `data=`, `timeout=`, `allow_redirects=`, dll.) |

### Kelas `Session` — untuk alur bertahap

```python
Session(profile="chrome", retries=2, retry_wait=1.5)
```

| Method | Fungsi |
|---|---|
| `s.get(url, **kw)` | Ambil halaman |
| `s.post(url, **kw)` | Kirim data |
| `s.request(method, url, **kw)` | Method bebas |
| `s.cookies_dict()` | Lihat semua cookie saat ini |
| `s.close()` | Tutup koneksi |

### Nama profil singkat

```python
from antibot import PROFILES
print(PROFILES)
```

```
{
  'chrome': 'chrome131',
  'chrome_new': 'chrome146',
  'chrome_android': 'chrome131_android',
  'firefox': 'firefox133',
  'safari': 'safari180',
  'safari_ios': 'safari180_ios',
  'edge': 'edge101',
  'tor': 'tor145',
}
```

Atau tulis versi persisnya langsung: `profile="chrome124"`, `profile="firefox144"`.

### Menyerahkan cookie ke tool lain

```python
with Session("chrome131") as s:
    s.get("https://target.com")
    cookies = s.cookies_dict()
    # pakai cookies ini di tempat lain, mis. dikirim ke program lain
```

---

## Daftar Browser yang Didukung

50+ profil siap pakai:

| Keluarga | Versi |
|---|---|
| **Chrome** | 99, 100, 101, 104, 107, 110, 116, 119, 120, 123, 124, 131, 133a, 136, 142, 145, 146, 150 |
| **Chrome Android** | 99, 131 |
| **Edge** | 99, 101 |
| **Firefox** | 133, 135, 144, 147 |
| **Safari** | 15.3, 15.5, 17.0, 17.2 (iOS), 18.0, 18.0 (iOS), 18.4, 18.4 (iOS), 26.0 |
| **Tor** | 145 |

Setiap profil menghasilkan sidik jari TLS yang **berbeda** — sudah diverifikasi.

---

## Apa yang Bisa dan Tidak Bisa Dilakukan

Ini bagian penting. Bacalah sebelum mengharapkan hasil.

### ✅ Bisa

| Kemampuan | Keterangan |
|---|---|
| Lolos pemeriksaan sidik jari TLS (JA3/JA4) | Terverifikasi pada situs uji Cloudflare |
| Lolos pemeriksaan sidik jari HTTP/2 | Termasuk fingerprint khas Akamai |
| Urutan header seperti browser asli | Chrome, Firefox, Safari masing-masing punya pola sendiri |
| Kelengkapan header | Header yang kurang ditambal otomatis |
| Cookie bertahan antar permintaan | Seperti browser asli |

**Hasil tes nyata:**

```
nowsecure.nl (situs uji Cloudflare)  → HTTP 200  ✅
```

### ❌ Tidak bisa

| Keterbatasan | Kenapa |
|---|---|
| **Cloudflare Turnstile** | Butuh menjalankan JavaScript — program ini tidak punya mesin JS |
| **Akamai `_abck` sensor** | Butuh menjalankan JavaScript |
| **DataDome slider** | Butuh browser sungguhan |
| **Captcha gambar** | Tidak ada solver, dan tidak akan ditambahkan |

Situs seperti `g2.com` dan `trustpilot.com` **tetap 403** karena mereka memerlukan eksekusi JavaScript, bukan sekadar sidik jari TLS yang benar.

> **Kalau butuh melewati tantangan JavaScript:** jalankan browser sungguhan (misalnya Playwright) untuk mengambil cookie hasil tantangan, lalu serahkan cookie itu ke `Session` di sini. Kombinasi ini jauh lebih kuat daripada salah satu saja.

---

## Pertanyaan yang Sering Ditanyakan

**Apakah ini legal?**
Program ini hanya mengubah cara koneksi Anda terlihat. Legalitasnya bergantung pada *apa yang Anda lakukan* dengannya — mematuhi atau melanggar Terms of Service situs tujuan, dan hukum setempat. Alat ini netral; penggunaannya tanggung jawab Anda.

**Apakah ini lebih baik dari Selenium/Playwright?**
Berbeda kegunaan. Program ini jauh lebih ringan (tanpa browser, hemat RAM) dan cepat. Selenium/Playwright lebih kuat karena bisa menjalankan JavaScript. Untuk scraping skala besar, program ini lebih efisien. Untuk situs dengan tantangan JS, Playwright lebih tepat.

**Kenapa hasilnya masih 403?**
Kemungkinan: (1) situs butuh JavaScript, (2) profil browser terlalu lama, (3) IP Anda diblokir, (4) perlu cookie dari kunjungan halaman utama dulu. Lihat [Pemecahan Masalah](#pemecahan-masalah).

**Apakah perlu ganti nama browser manual?**
Tidak. Program ini sudah mengatur User-Agent, `sec-ch-ua`, `Accept-Language`, dan header lainnya secara otomatis dan konsisten dengan profil yang dipilih.

**Apakah aman? Apakah ada koneksi tersembunyi?**
Aman. Program ini **hanya** terhubung ke alamat yang Anda tentukan sendiri. Tidak ada server perantara, tidak ada telemetri, tidak ada koneksi ke pihak ketiga. Seluruh kode bisa Anda baca — 197 baris.

**Bisa dipakai untuk situs apa saja?**
Bisa dicoba ke situs apa pun. Kalau butuh JavaScript, akan gagal — dan itu memang batas teknisnya, bukan bug.

---

## Cara Kerja (versi teknis)

Bagian ini untuk yang penasaran isi dapur.

### Masalahnya

Saat script Python terhubung ke HTTPS, ia melakukan "jabat tangan" TLS. Di dalam jabat tangan itu ada daftar algoritma enkripsi, urutan, dan ekstensi yang dikirim client. Susunan itu membentuk **sidik jari** (JA3/JA4) yang berbeda untuk setiap program.

`requests` biasa punya sidik jari yang khas dan mudah dikenali. Itu sebabnya langsung diblokir.

### Solusinya

Modul ini memakai `curl_cffi`, yang membungkus **BoringSSL** (pustaka enkripsi milik Google, dipakai Chrome) dengan profil ClientHello browser asli. Hasilnya: sidik jari TLS yang **identik** dengan browser yang ditiru.

Tiga lapisan ditangani sekaligus:

```
Lapisan 1 — TLS (JA3/JA4)
    └─ BoringSSL + profil ClientHello browser asli

Lapisan 2 — HTTP/2 (Akamai fingerprint)
    └─ Setelan frame & prioritas sesuai browser

Lapisan 3 — Header HTTP
    └─ _prepare_headers(): tambal yang kurang, urutkan sesuai browser
```

### Urutan header

Browser asli mengirim header dalam urutan yang konsisten. Chrome selalu menaruh `Accept` sebelum `Cookie`, misalnya. Script yang mengirim header dengan urutan acak langsung ketahuan.

Fungsi `_prepare_headers()` menyusun ulang header mengikuti urutan browser asli, dan menambal header yang hilang (`sec-ch-ua`, `sec-fetch-*`, `priority`, dll.) agar jumlahnya tidak lebih sedikit dari browser sungguhan.

### Struktur file

```
antibot-fetch/
├── antibot.py     # seluruh program (197 baris)
└── README.md
```

### Persyaratan teknis

- Python 3.8+
- Satu dependensi: `curl_cffi`
- Berjalan di Windows, macOS, Linux

### Verifikasi mandiri

```bash
# sidik jari TLS harus BERBEDA tiap profil
python -c "from curl_cffi import requests; print(requests.get('https://tls.browserleaks.com/json', impersonate='chrome131').json()['ja3_hash'])"
python -c "from curl_cffi import requests; print(requests.get('https://tls.browserleaks.com/json', impersonate='firefox133').json()['ja3_hash'])"
```

Kalau hash-nya sama, profil tidak diterapkan.

---

## Pemecahan Masalah

**`ModuleNotFoundError: No module named 'curl_cffi'`**

```
pip install curl_cffi
```

Kalau masih gagal, pastikan pip dan python menunjuk instalasi yang sama:

```
python -m pip install curl_cffi
```

**`ModuleNotFoundError: No module named 'antibot'`**

File `antibot.py` tidak berada di folder yang sama dengan script Anda. Pindahkan, atau tambahkan folder-nya ke path:

```python
import sys
sys.path.insert(0, r"C:\path\ke\folder\antibot")
from antibot import fetch
```

**Masih dapat 403 / 429**

Coba berurutan:

1. Ganti profil: `fetch(url, profile="chrome146")` — versi lebih baru
2. Kunjungi halaman utama dulu, baru halaman target:
   ```python
   with Session("chrome131") as s:
       s.get("https://target.com")
       r = s.get("https://target.com/data")
   ```
3. Beri jeda antar permintaan — jangan membanjiri server
4. Periksa apakah IP Anda diblokir (coba ganti jaringan / VPN)
5. Kalau tetap gagal, situs itu kemungkinan butuh JavaScript — lihat [batasan](#-tidak-bisa)

**`curl: (35) SSL connect error` atau koneksi terputus**

Server memutus koneksi karena tidak menyukai profilnya. Coba profil lain, dan pastikan `retries` aktif (sudah default).

**`session.cookies.jar` error**

Gunakan `session.cookies.get_dict()`, bukan iterasi langsung ke `.jar`.

**Hasilnya 200 tapi cookie kosong**

Itu **berhasil**, bukan gagal. Beberapa situs tidak memberi cookie sama sekali saat Anda lolos dari sidik jari TLS saja.

---

## Lisensi

MIT — bebas dipakai, diubah, dan dibagikan.

## Penafian

Alat ini mengubah tampilan koneksi Anda di mata sistem keamanan website. Tanggung jawab kepatuhan terhadap Terms of Service situs tujuan dan hukum yang berlaku sepenuhnya ada pada pengguna. Penulis tidak bertanggung jawab atas penyalahgunaan.

---

## Asal-usul

Modul ini dibuat setelah menganalisis `ProTLS 1.0` — sebuah alat komersial yang dibungkus Inno Setup + PyInstaller. ProTLS memakai `curl_cffi` untuk kemampuan intinya, **tapi juga membuka koneksi tersembunyi ke gateway pihak ketiga** (`wordlister.dsyydfydfbbsd.xyz:9002`) yang tidak dijelaskan di dokumentasinya.

Modul ini mengambil bagian yang berguna — tanpa gateway tersembunyi, tanpa telemetri, tanpa kejutan.
