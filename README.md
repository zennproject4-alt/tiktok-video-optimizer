# TikTok Video Optimizer

Website untuk mengoptimalkan file video agar lebih siap diunggah ke TikTok, **tanpa mengubah isi visual video sama sekali**.

## Yang dilakukan aplikasi ini
- Menganalisis struktur teknis video (codec, resolusi, bitrate, fps, dll)
- Mengoptimalkan struktur container MP4 (faststart)
- Membersihkan metadata non-esensial
- Memberikan laporan before/after

## Yang TIDAK dilakukan aplikasi ini
- Tidak melakukan AI upscale
- Tidak mengubah warna, brightness, contrast, atau sharpness
- Tidak mengubah isi visual video dalam bentuk apapun (proses menggunakan stream copy / `-c copy`, bukan re-encode)

## Tech Stack
- Backend: Python, FastAPI, FFmpeg (subprocess)
- Frontend: HTML, CSS, vanilla JavaScript

## Prasyarat
- Python 3.10+
- FFmpeg (download dari https://www.gyan.dev/ffmpeg/builds/, tambahkan ke PATH)

## Cara menjalankan

### 1. Setup backend
\`\`\`bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
\`\`\`

Backend akan berjalan di `http://127.0.0.1:8000`
Dokumentasi API otomatis tersedia di `http://127.0.0.1:8000/docs`

### 2. Jalankan frontend
Buka `frontend/index.html` langsung di browser.

## Alur penggunaan
1. Upload video (`POST /upload`)
2. Video otomatis dianalisis (`GET /analyze/{file_id}`)
3. Klik "Optimalkan Video" (`POST /optimize/{file_id}`)
4. Download hasil optimasi (`GET /download/{file_id}`)

## Struktur Project
\`\`\`
tiktok-video-optimizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # Endpoint FastAPI
│   │   ├── video_analyzer.py    # Modul analisis (ffprobe)
│   │   ├── video_optimizer.py   # Modul optimasi (ffmpeg)
│   │   ├── uploads/             # File asli dari user
│   │   └── outputs/             # File hasil optimasi
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
\`\`\`