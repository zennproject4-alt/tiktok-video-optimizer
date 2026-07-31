import shutil
import uuid
import subprocess
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.video_analyzer import build_analysis_report

from app.video_optimizer import optimize_video, OptimizationError

from fastapi.responses import FileResponse

from app.tiktok_compliance import check_tiktok_compliance

app = FastAPI(title="TikTok Video Optimizer API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # untuk development, nanti bisa dipersempit
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direktori dasar project (folder app/)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Pastikan folder ada saat aplikasi start
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Ekstensi video yang kita izinkan untuk sekarang
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

@app.get("/")
def read_root():
    return {"status": "ok", "message": "TikTok Video Optimizer API is running"}


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # 1. Validasi ekstensi file
    original_ext = Path(file.filename).suffix.lower()
    if original_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung: {original_ext}. "
                   f"Gunakan salah satu dari {sorted(ALLOWED_EXTENSIONS)}",
        )

    # 2. Buat nama file unik
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}{original_ext}"
    saved_path = UPLOAD_DIR / saved_filename

    # 3. Simpan file sambil mengecek ukuran per-chunk
    total_size = 0
    chunk_size = 1024 * 1024  # 1MB per chunk

    try:
        with saved_path.open("wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    buffer.close()
                    saved_path.unlink(missing_ok=True)  # hapus file yang sudah kepalang ditulis
                    raise HTTPException(
                        status_code=413,
                        detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
                    )
                buffer.write(chunk)
    finally:
        await file.close()

    return {
        "status": "ok",
        "file_id": file_id,
        "original_filename": file.filename,
        "saved_as": saved_filename,
        "size_bytes": saved_path.stat().st_size,
    }

@app.get("/analyze/{file_id}")
def analyze_video(file_id: str):
    matches = list(UPLOAD_DIR.glob(f"{file_id}.*"))

    if not matches:
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    file_path = matches[0]

    try:
        report = build_analysis_report(file_path)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis video: {e.stderr}")

    compliance = check_tiktok_compliance(report)

    return {
        "status": "ok",
        "file_id": file_id,
        "filename": file_path.name,
        "analysis": report,
        "tiktok_compliance": compliance,
    }

@app.post("/optimize/{file_id}")
def optimize(file_id: str):
    matches = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    input_path = matches[0]
    output_filename = f"{file_id}_optimized.mp4"
    output_path = OUTPUT_DIR / output_filename

    try:
        report_before = build_analysis_report(input_path)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis file asli: {e.stderr}")

    try:
        optimize_video(input_path, output_path)
    except OptimizationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        report_after = build_analysis_report(output_path)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis hasil optimasi: {e.stderr}")

    return {
        "status": "ok",
        "file_id": file_id,
        "output_filename": output_filename,
        "before": report_before,
        "after": report_after,
    }

@app.get("/download/{file_id}")
def download_video(file_id: str):
    output_filename = f"{file_id}_optimized.mp4"
    output_path = OUTPUT_DIR / output_filename

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File hasil optimasi tidak ditemukan")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=output_filename,
    )

@app.delete("/cleanup/{file_id}")
def cleanup_files(file_id: str):
    deleted_files = []

    for folder in [UPLOAD_DIR, OUTPUT_DIR]:
        for match in folder.glob(f"{file_id}*"):
            match.unlink()
            deleted_files.append(match.name)

    if not deleted_files:
        raise HTTPException(status_code=404, detail="Tidak ada file yang ditemukan untuk file_id ini")

    return {"status": "ok", "deleted_files": deleted_files}