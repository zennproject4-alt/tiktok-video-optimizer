FROM python:3.12-slim

# Install FFmpeg dari repository resmi Debian (base image Python ini berbasis Debian)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependency Python dulu (supaya layer ini di-cache, build berikutnya lebih cepat)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY app ./app

# Buat folder uploads & outputs (jaga-jaga kalau .gitkeep tidak ikut ter-copy)
RUN mkdir -p app/uploads app/outputs

# Render menyediakan variable PORT secara dinamis, kita pakai itu
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]