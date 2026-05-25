# Backend Python

Panduan ini adalah pintu masuk untuk backend `ParticleVisualizer`.

> Catatan penting: backend aktif saat ini **belum memakai Flask**. Implementasi berjalan melalui `main.py` dan menyiarkan hasil deteksi tangan ke WebSocket lokal untuk dipakai frontend React.

## Ringkasan

| Item | Nilai |
| --- | --- |
| Python | 3.12.4 |
| Entry point | `main.py` |
| WebSocket | `ws://localhost:8765` |
| Dokumentasi teknis | [Backend Python detail](./python-backend.md) |

## Setup environment

### 1) Buat `.venv`

Jalankan dari root project:

```powershell
py -3.12 -m venv .venv
```

### 2) Aktifkan `.venv`

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```

Jika environment sudah ada, cukup aktifkan saja.

## Install dependency

```powershell
pip install -r requirements.txt
```

## Menjalankan backend

```powershell
python main.py
```

## Yang dilakukan backend

Backend Python menangani:

- membaca input kamera
- mendeteksi tangan dan gesture
- menyiarkan data landmark ke WebSocket lokal
- menjadi sumber data untuk frontend React

## Lihat dokumentasi teknis

Untuk penjelasan lebih lengkap tentang struktur, troubleshooting, dan alur kerja backend, baca [Backend Python detail](./python-backend.md).
