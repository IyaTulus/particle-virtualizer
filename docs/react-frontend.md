# Frontend React

Dokumen ini menjelaskan cara menjalankan frontend React untuk `ParticleVisualizer`.

## Gambaran umum

Frontend berada di folder `web/` dan menggunakan:

- React
- Vite
- Three.js / React Three Fiber

Frontend ini menerima data gesture dan landmark dari WebSocket lokal yang disediakan oleh backend Python.

## Prasyarat

Pastikan kamu sudah menyiapkan:

- Node.js versi LTS
- npm
- Backend Python sudah berjalan di `ws://localhost:8765`

## Install npm dependencies

Masuk ke folder frontend lalu install dependency:

```powershell
cd web
npm install
```

## Cara menjalankan frontend

Jalankan Vite dev server:

```powershell
cd web
npm run dev
```

Setelah itu buka URL yang ditampilkan terminal, biasanya:

- `http://localhost:5173`

## Build untuk production

Jika ingin membuat build produksi:

```powershell
cd web
npm run build
```

## Alur menjalankan project

Urutan yang disarankan:

1. Aktifkan `.venv`
2. Install `requirements.txt`
3. Jalankan `python main.py`
4. Jalankan frontend dengan `npm install` lalu `npm run dev`
5. Buka aplikasi di browser

## Catatan troubleshooting

- Jika halaman kosong, pastikan backend Python sudah aktif.
- Jika koneksi WebSocket gagal, cek apakah port `8765` terbuka.
- Jika build gagal, hapus `node_modules` lalu install ulang dengan `npm install`.
