# Contribution Guide

Terima kasih sudah ingin berkontribusi ke `ParticleVisualizer`.

Panduan ini menjelaskan alur kontribusi yang disarankan agar perubahan tetap rapi, mudah direview, dan konsisten dengan arah project.

## Prinsip kontribusi

- Buat perubahan yang kecil, jelas, dan mudah diuji.
- Jaga agar kontribusi tetap selaras dengan tema project: visual, interaktif, dan berfokus pada gesture / partikel.
- Boleh menggunakan AI, boleh juga kreasi sendiri, selama hasil akhirnya tetap orisinal dan relevan.
- Hindari menggabungkan banyak perubahan besar dalam satu PR.

## Alur kerja yang disarankan

### 1) Buat branch sendiri

Sebelum mulai bekerja, buat branch baru dari `develop`.

Contoh nama branch:

- `feature/new-particle-style`
- `feature/gesture-visual-update`
- `improvement/docs-modernization`
- `experiment/ai-generated-shapes`

Gunakan nama branch yang singkat, deskriptif, dan mudah dipahami.

### 2) Kerjakan perubahan di branch tersebut

Lakukan perubahan sesuai ide kontribusi kamu, misalnya:

- visual baru untuk particle
- bentuk atau gaya baru untuk gesture
- perbaikan dokumentasi
- penyempurnaan UX frontend
- eksperimen berbasis AI yang tetap konsisten dengan project

Pastikan hasilnya sudah diuji sebelum dibuat PR.

### 3) Buat Pull Request ke `develop`

Setelah selesai, buka Pull Request dari branch kamu ke branch `develop`.

Pastikan deskripsi PR berisi:

- ringkasan perubahan
- alasan perubahan
- hasil pengujian
- screenshot atau preview jika ada perubahan visual

### 4) Tag admin untuk review

Setelah PR dibuat, tag admin atau maintainer project agar review bisa segera dilakukan.

Contoh catatan di PR:

- `@admin mohon review`
- `@maintainer mohon review`
- `Tag admin untuk pengecekan visual`

Jika ada revisi dari reviewer, update branch yang sama lalu push kembali sampai siap di-merge.

## Hal yang membantu proses review

- Sertakan screenshot atau rekaman singkat jika perubahan bersifat visual.
- Jelaskan folder atau file yang berubah.
- Tulis langkah testing yang sudah dilakukan.
- Jika kontribusi berbasis AI, jelaskan bagaimana hasilnya disesuaikan dengan kebutuhan project.

## Checklist sebelum mengirim PR

- [ ] Branch dibuat dari `develop`
- [ ] Perubahan sudah diuji
- [ ] Tidak ada file yang tidak sengaja ikut berubah
- [ ] Deskripsi PR jelas dan ringkas
- [ ] Admin / maintainer sudah ditandai untuk review

## Catatan penting

Kami menghargai kontribusi yang kreatif, bersih, dan mudah dipelihara. Jika kamu membuat visual baru dengan AI atau kreasi manual, pastikan hasil akhirnya tetap nyaman dipakai dan sejalan dengan identitas `ParticleVisualizer`.
