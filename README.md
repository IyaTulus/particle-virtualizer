# Particle Visualizer

`ParticleVisualizer` adalah project eksperimen visualisasi partikel berbasis deteksi tangan dan bahasa isyarat.

Project ini terdiri dari dua bagian utama:

- **Backend Python** untuk deteksi tangan, gesture, dan WebSocket broadcaster
- **Frontend React** untuk visualisasi 3D berbasis Vite + Three.js

## Ringkasan cepat

- **Python yang dipakai:** 3.12.4
- **Backend:** `main.py`
- **Frontend:** `web/`
- **Dokumentasi tambahan:** `docs/`

## Cara menjalankan project

Urutan yang disarankan:

1. Siapkan dan aktifkan `.venv`
2. Install dependency Python dari `requirements.txt`
3. Jalankan backend Python
4. Masuk ke folder `web/`
5. Install dependency npm
6. Jalankan frontend React

Panduan lengkap ada di:

- [Flask / Backend Python](docs/flask.md)
- [Backend Python detail](docs/python-backend.md)
- [Frontend React](docs/react-frontend.md)
- [Alphabet Bahasa Isyarat](docs/sign-language-alphabet.md)

## Visual reference

Berikut referensi alfabet bahasa isyarat yang digunakan sebagai acuan gesture:

![Alphabet bahasa isyarat](https://i.pinimg.com/originals/5d/38/ed/5d38ed4f4ed71134c84c19fcd2a6aaa0.jpg)

Lihat penjelasan huruf dan bentuk tangannya di [dokumentasi alfabet bahasa isyarat](docs/sign-language-alphabet.md).

## Struktur proyek

- `main.py` — entry point backend Python
- `hand_tacking/` — helper deteksi tangan dan stabilisasi gesture
- `particles/` — engine partikel
- `recognition/` — translasi gesture ke teks
- `web/` — frontend React
- `docs/` — dokumentasi publik project

## Catatan implementasi

Backend saat ini **belum memakai Flask**. Implementasi aktif berjalan melalui Python script utama dan WebSocket lokal. Dokumentasi backend tetap dipisah agar mudah diikuti dan mudah dikembangkan kalau nanti backend dipindahkan ke Flask.

