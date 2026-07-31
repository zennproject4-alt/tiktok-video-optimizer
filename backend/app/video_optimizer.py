import subprocess
from pathlib import Path


class OptimizationError(Exception):
    """Custom exception untuk error yang terjadi saat proses optimasi video."""
    pass


def optimize_video(input_path: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-map", "0",
        "-map_metadata", "-1",
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Ambil beberapa baris terakhir dari stderr FFmpeg, biasanya di situ pesan error intinya
        error_lines = result.stderr.strip().splitlines()
        short_error = "\n".join(error_lines[-5:]) if error_lines else "Unknown FFmpeg error"

        raise OptimizationError(
            f"FFmpeg gagal memproses video. Kemungkinan codec tidak didukung untuk stream copy.\n"
            f"Detail: {short_error}"
        )