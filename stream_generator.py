#!/usr/bin/env python3
import subprocess
import requests
import os
from pathlib import Path
import shutil

# ================== AYARLAR ==================
INPUT = "https://cdn.codenet.lol/streamgo/stremgo123/4866.m3u8"
LOGO_URL = "https://raw.githubusercontent.com/mutlumedya/yay-n-1/refs/heads/main/logo.png"

OUTPUT_DIR = Path("./hls_output")
TEMP_DIR = Path("./temp_hls")

# =============================================

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

def download_logo():
    logo_path = TEMP_DIR / "logo.png"
    try:
        r = requests.get(LOGO_URL, timeout=15)
        r.raise_for_status()
        logo_path.write_bytes(r.content)
        print("✅ Logo indirildi")
        return str(logo_path)
    except:
        print("⚠️ Logo indirilemedi")
        return None

def generate_hls():
    logo_path = download_logo()
    
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-i", INPUT,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-b:v", "1100k",
        "-maxrate", "1100k",
        "-bufsize", "2000k",
        "-g", "30",
        "-c:a", "aac",
        "-b:a", "96k",
        "-f", "hls",
        "-hls_time", "4",
        "-hls_list_size", "10",
        "-hls_flags", "delete_segments+append_list+omit_endlist",
        "-hls_segment_filename", str(TEMP_DIR / "seg_%05d.ts"),
        str(TEMP_DIR / "playlist.m3u8")
    ]
    
    if logo_path:
        cmd.insert(-8, "-i")
        cmd.insert(-8, logo_path)
        cmd.insert(-8, "-filter_complex")
        cmd.insert(-8, f"[0:v][1:v]overlay=W-w-15:15:format=auto,format=yuv420p")
    
    try:
        print("📡 HLS oluşturuluyor...")
        subprocess.run(cmd, check=True, timeout=60)
        print("✅ HLS oluşturuldu!")
        return True
    except:
        return False

def deploy_to_pages():
    print("📤 Yayın hazırlanıyor...")
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            shutil.copy2(file, OUTPUT_DIR / file.name)
    
    # index.html oluştur
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📺 Canlı Yayın</title>
    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
    <style>
        body { margin: 0; background: #000; }
        .video-js { width: 100%; height: 100vh; }
    </style>
</head>
<body>
    <video id="video" class="video-js vjs-default-skin" controls autoplay>
        <source src="playlist.m3u8" type="application/x-mpegURL">
    </video>
    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
    <script>videojs('video');</script>
</body>
</html>'''
    (OUTPUT_DIR / "index.html").write_text(html)
    print("✅ index.html oluşturuldu")

def main():
    print("🚀 Başlatılıyor...")
    generate_hls()
    deploy_to_pages()
    print("✅ Tamam!")

if __name__ == "__main__":
    main()
