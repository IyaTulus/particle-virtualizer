# Flask / Backend Python

Dokumen ini adalah pintu masuk untuk bagian backend project.

> Catatan penting: implementasi yang aktif saat ini **belum memakai Flask**. Backend berjalan melalui `main.py` dan menyiarkan hasil deteksi tangan ke WebSocket lokal untuk dipakai frontend React.

## Versi Python

- **Python 3.12.4**

## Setup `.venv`

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

## Install requirements

```powershell
pip install -r requirements.txt
```

## Cara menjalankan backend

```powershell
python main.py
```

## Detail lengkap

Untuk penjelasan yang lebih detail tentang environment, dependency, dan troubleshooting, baca:

- [Panduan backend Python](./python-backend.md)
