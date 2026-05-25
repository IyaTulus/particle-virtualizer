# Backend Python

Dokumen ini menjelaskan cara menjalankan backend Python pada project `ParticleVisualizer`.

> Catatan penting: backend saat ini **belum menggunakan Flask**. Implementasi yang aktif berjalan melalui `main.py` dan menyiarkan data hand tracking ke WebSocket lokal untuk dikonsumsi frontend React.

## Versi Python

Project ini diuji menggunakan:

- **Python 3.12.4**

## Prasyarat

Pastikan kamu sudah menyiapkan:

- Python 3.12.x
- Kamera yang berfungsi
- Repository ini sudah di-clone ke komputer lokal

## Setup `.venv`

### Windows PowerShell

Jalankan dari root project:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Jika environment `.venv` sudah tersedia, cukup aktifkan saja:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Cek interpreter aktif

Setelah aktivasi, pastikan Python yang dipakai berasal dari `.venv`:

```powershell
python --version
where python
```

## Install dependencies

Install semua package yang dibutuhkan dengan:

```powershell
pip install -r requirements.txt
```

## Cara menjalankan backend

Jalankan dari root project:

```powershell
python main.py
```

## Apa yang dilakukan backend

Backend Python bertugas untuk:

- membaca input kamera
- mendeteksi tangan dan gesture
- menyiarkan data landmark ke WebSocket di `ws://localhost:8765`
- menghubungkan hasil deteksi ke visualisasi particle / browser

## Catatan troubleshooting

- Jika kamera gagal dibuka, pastikan tidak sedang dipakai aplikasi lain.
- Jika frontend tidak menerima data, pastikan backend sudah berjalan dan port `8765` belum dipakai proses lain.
- Jika `pip install` gagal, cek kembali bahwa `.venv` sudah aktif sebelum instalasi.
