import json
import subprocess
from pathlib import Path
from typing import Any


def probe_video(file_path: Path) -> dict[str, Any]:
    """
    Menjalankan ffprobe pada file video dan mengembalikan data mentah
    dalam bentuk dictionary. Tidak mengubah file sama sekali — read-only.
    """
    command = [
        "ffprobe",
        "-v", "error",              # sembunyikan log yang tidak perlu
        "-show_format",             # info container (durasi, bitrate, dll)
        "-show_streams",            # info tiap stream (video, audio)
        "-print_format", "json",    # output dalam JSON
        str(file_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def check_faststart(file_path: Path) -> bool:
    """
    Mengecek apakah moov atom berada di awal file (faststart = True)
    atau di akhir file (faststart = False).
    Dilakukan dengan membaca urutan atom MP4 secara manual,
    TANPA mengubah file.
    """
    with file_path.open("rb") as f:
        # Baca 4KB pertama untuk mencari atom moov/mdat di awal
        # Kalau moov ditemukan sebelum mdat, berarti sudah faststart
        chunk = f.read(64 * 1024)  # baca 64KB pertama, cukup untuk sebagian besar kasus

    moov_pos = chunk.find(b"moov")
    mdat_pos = chunk.find(b"mdat")

    if moov_pos == -1:
        # moov tidak ditemukan di awal file -> kemungkinan besar ada di akhir
        return False

    if mdat_pos == -1:
        # mdat belum ditemukan dalam chunk awal, tapi moov sudah ada duluan
        return True

    return moov_pos < mdat_pos


def build_analysis_report(file_path: Path) -> dict[str, Any]:
    """
    Menyusun laporan analisis video yang ringkas dan mudah dibaca,
    diambil dari data mentah ffprobe.
    """
    raw = probe_video(file_path)

    format_info = raw.get("format", {})
    streams = raw.get("streams", [])

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    report: dict[str, Any] = {
        "file_size_bytes": int(format_info.get("size", 0)),
        "duration_seconds": float(format_info.get("duration", 0)),
        "container_format": format_info.get("format_name", "unknown"),
        "overall_bitrate": int(format_info.get("bit_rate", 0)),
        "is_faststart": check_faststart(file_path),
    }

    if video_stream:
        # frame rate biasanya dalam bentuk pecahan string, misal "30000/1001"
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        num, den = r_frame_rate.split("/")
        fps = round(int(num) / int(den), 2) if int(den) != 0 else 0

        report["video"] = {
            "codec": video_stream.get("codec_name", "unknown"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": fps,
            "bitrate": int(video_stream.get("bit_rate", 0)) if video_stream.get("bit_rate") else None,
            "pixel_format": video_stream.get("pix_fmt"),
        }
    else:
        report["video"] = None

    if audio_stream:
        report["audio"] = {
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": audio_stream.get("sample_rate"),
            "channels": audio_stream.get("channels"),
            "bitrate": int(audio_stream.get("bit_rate", 0)) if audio_stream.get("bit_rate") else None,
        }
    else:
        report["audio"] = None

    return report