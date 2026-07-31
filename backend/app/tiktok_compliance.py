from typing import Any

# ============================================================
# Konstanta rekomendasi TikTok (per data terkini, bisa berubah
# sewaktu-waktu — cek ulang berkala ke dokumentasi resmi TikTok)
# ============================================================

RECOMMENDED_ASPECT_RATIO = (9, 16)
ACCEPTED_ASPECT_RATIOS = [(9, 16), (1, 1), (16, 9)]

RECOMMENDED_RESOLUTION = (1080, 1920)
MIN_RESOLUTION = (540, 960)

ALLOWED_VIDEO_CODECS = {"h264", "hevc", "h265"}
ALLOWED_AUDIO_CODECS = {"aac"}

MAX_FPS_STANDARD = 30
MAX_FPS_HIGH = 60

RECOMMENDED_MIN_BITRATE = 2_500_000  # 2.5 Mbps, dalam bits per second
MIN_VIABLE_BITRATE = 516_000         # 516 kbps

DEFAULT_MAX_DURATION_SECONDS = 3 * 60      # 3 menit (batas default sebagian besar akun)
EXTENDED_MAX_DURATION_SECONDS = 10 * 60    # 10 menit (akun dengan akses diperluas)

MAX_FILE_SIZE_BYTES_WEB = 500 * 1024 * 1024        # 500MB (web/feed upload)
MAX_FILE_SIZE_BYTES_MOBILE_SAFE = 72 * 1024 * 1024  # 72MB (batas aman, mengikuti Android)


def _closest_aspect_ratio_label(width: int, height: int) -> str:
    """Menentukan rasio aspek video dalam bentuk label mudah dibaca."""
    if not width or not height:
        return "unknown"

    ratio = width / height

    candidates = {
        "9:16 (vertical)": 9 / 16,
        "1:1 (square)": 1 / 1,
        "16:9 (horizontal)": 16 / 9,
    }

    closest_label = min(candidates, key=lambda label: abs(candidates[label] - ratio))
    return closest_label


def check_tiktok_compliance(analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Membandingkan hasil analisis video terhadap rekomendasi TikTok.
    Fungsi ini HANYA membaca data, tidak pernah mengubah video.
    """
    checks: list[dict[str, Any]] = []

    video = analysis.get("video")
    audio = analysis.get("audio")

    # --- Cek resolusi & aspect ratio ---
    if video:
        width = video.get("width") or 0
        height = video.get("height") or 0
        aspect_label = _closest_aspect_ratio_label(width, height)

        if aspect_label == "9:16 (vertical)":
            checks.append({
                "category": "aspect_ratio",
                "level": "pass",
                "message": f"Rasio aspek {aspect_label} — sesuai rekomendasi utama TikTok.",
            })
        else:
            checks.append({
                "category": "aspect_ratio",
                "level": "warning",
                "message": f"Rasio aspek {aspect_label} — diterima TikTok, "
                           f"tapi 9:16 vertical lebih direkomendasikan untuk jangkauan maksimal.",
            })

        # Tentukan sisi panjang & pendek video, tidak peduli orientasinya
        long_side = max(width, height)
        short_side = min(width, height)

        recommended_long = max(RECOMMENDED_RESOLUTION)   # 1920
        recommended_short = min(RECOMMENDED_RESOLUTION)  # 1080
        min_long = max(MIN_RESOLUTION)                   # 960
        min_short = min(MIN_RESOLUTION)                  # 540

        if long_side >= recommended_long and short_side >= recommended_short:
            checks.append({
                "category": "resolution",
                "level": "pass",
                "message": f"Resolusi {width}x{height} — sudah sesuai atau melebihi rekomendasi (setara 1080x1920).",
            })
        elif long_side >= min_long and short_side >= min_short:
            checks.append({
                "category": "resolution",
                "level": "warning",
                "message": f"Resolusi {width}x{height} — di atas minimum, tapi di bawah rekomendasi (setara 1080x1920).",
            })
        else:
            checks.append({
                "category": "resolution",
                "level": "fail",
                "message": f"Resolusi {width}x{height} — di bawah minimum yang disarankan (setara 540x960).",
            })

        # --- Cek codec video ---
        codec = (video.get("codec") or "").lower()
        if codec in ALLOWED_VIDEO_CODECS:
            checks.append({
                "category": "video_codec",
                "level": "pass",
                "message": f"Codec video '{codec}' didukung TikTok.",
            })
        else:
            checks.append({
                "category": "video_codec",
                "level": "fail",
                "message": f"Codec video '{codec}' kemungkinan tidak didukung. Gunakan H.264 atau H.265.",
            })

        # --- Cek frame rate ---
        fps = video.get("fps") or 0
        if fps <= MAX_FPS_STANDARD:
            checks.append({
                "category": "frame_rate",
                "level": "pass",
                "message": f"Frame rate {fps}fps — sesuai standar TikTok.",
            })
        elif fps <= MAX_FPS_HIGH:
            checks.append({
                "category": "frame_rate",
                "level": "warning",
                "message": f"Frame rate {fps}fps — didukung untuk konten dengan gerakan cepat, tapi di atas standar 30fps.",
            })
        else:
            checks.append({
                "category": "frame_rate",
                "level": "warning",
                "message": f"Frame rate {fps}fps — cukup tinggi, TikTok mungkin melakukan penyesuaian saat proses upload.",
            })

    else:
        checks.append({
            "category": "video_stream",
            "level": "fail",
            "message": "Tidak ditemukan stream video dalam file ini.",
        })

    # --- Cek codec audio ---
    if audio:
        audio_codec = (audio.get("codec") or "").lower()
        if audio_codec in ALLOWED_AUDIO_CODECS:
            checks.append({
                "category": "audio_codec",
                "level": "pass",
                "message": f"Codec audio '{audio_codec}' didukung TikTok.",
            })
        else:
            checks.append({
                "category": "audio_codec",
                "level": "warning",
                "message": f"Codec audio '{audio_codec}' mungkin perlu dikonversi ke AAC untuk kompatibilitas terbaik.",
            })
    else:
        checks.append({
            "category": "audio_stream",
            "level": "warning",
            "message": "Tidak ditemukan stream audio. Video tanpa audio tetap bisa diunggah, tapi pastikan ini disengaja.",
        })

    # --- Cek bitrate keseluruhan ---
    bitrate = analysis.get("overall_bitrate") or 0
    if bitrate >= RECOMMENDED_MIN_BITRATE:
        checks.append({
            "category": "bitrate",
            "level": "pass",
            "message": f"Bitrate {bitrate // 1000}kbps — sesuai rekomendasi untuk kualitas optimal.",
        })
    elif bitrate >= MIN_VIABLE_BITRATE:
        checks.append({
            "category": "bitrate",
            "level": "warning",
            "message": f"Bitrate {bitrate // 1000}kbps — masih diterima, tapi di bawah rekomendasi (2500kbps).",
        })
    else:
        checks.append({
            "category": "bitrate",
            "level": "warning",
            "message": f"Bitrate {bitrate // 1000}kbps — cukup rendah, kualitas video mungkin kurang optimal.",
        })

    # --- Cek durasi ---
    duration = analysis.get("duration_seconds") or 0
    if duration <= DEFAULT_MAX_DURATION_SECONDS:
        checks.append({
            "category": "duration",
            "level": "pass",
            "message": f"Durasi {duration:.1f} detik — dalam batas default (3 menit) untuk semua akun.",
        })
    elif duration <= EXTENDED_MAX_DURATION_SECONDS:
        checks.append({
            "category": "duration",
            "level": "warning",
            "message": f"Durasi {duration:.1f} detik — melebihi batas default 3 menit, "
                       f"memerlukan akun dengan akses upload diperluas (hingga 10 menit).",
        })
    else:
        checks.append({
            "category": "duration",
            "level": "fail",
            "message": f"Durasi {duration:.1f} detik — melebihi batas maksimum 10 menit untuk sebagian besar akun.",
        })

    # --- Cek ukuran file ---
    file_size = analysis.get("file_size_bytes") or 0
    if file_size <= MAX_FILE_SIZE_BYTES_MOBILE_SAFE:
        checks.append({
            "category": "file_size",
            "level": "pass",
            "message": f"Ukuran file {file_size / (1024*1024):.1f}MB — aman untuk semua platform (web & mobile).",
        })
    elif file_size <= MAX_FILE_SIZE_BYTES_WEB:
        checks.append({
            "category": "file_size",
            "level": "warning",
            "message": f"Ukuran file {file_size / (1024*1024):.1f}MB — diterima di web, "
                       f"tapi mungkin melebihi batas aplikasi mobile di beberapa perangkat.",
        })
    else:
        checks.append({
            "category": "file_size",
            "level": "fail",
            "message": f"Ukuran file {file_size / (1024*1024):.1f}MB — melebihi batas maksimum unggahan (500MB).",
        })

    # --- Kesimpulan keseluruhan ---
    levels = [c["level"] for c in checks]
    if "fail" in levels:
        overall = "fail"
    elif "warning" in levels:
        overall = "warning"
    else:
        overall = "pass"

    return {
        "overall_status": overall,
        "checks": checks,
    }