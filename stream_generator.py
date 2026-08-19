#!/usr/bin/env python3
import subprocess
import requests
import time
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

# ================== AYARLAR ==================
INPUT = os.environ.get('INPUT_URL', 'https://cdn.codenet.lol/streamgo/stremgo123/4866.m3u8')
LOGO_URL = "https://raw.githubusercontent.com/mutlumedya/yay-n-1/refs/heads/main/logo.png"
WORK_DIR = Path.home() / "zemtv"
HLS_DIR = WORK_DIR / "hls"
LOGO_PATH = WORK_DIR / "logo.png"

# Port'u environment'dan al veya otomatik bul
PORT = int(os.environ.get('PORT', 8080))

# =============================================

WORK_DIR.mkdir(exist_ok=True)
HLS_DIR.mkdir(exist_ok=True)

def get_local_ip():
    """Cihazın yerel IP adresini bul"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def download_logo():
    print("Logo indiriliyor...")
    try:
        r = requests.get(LOGO_URL, timeout=15)
        r.raise_for_status()
        LOGO_PATH.write_bytes(r.content)
        print("Logo indirildi →", LOGO_PATH)
        return True
    except Exception as e:
        print("Logo indirilemedi:", e)
        # Logo yoksa devam et
        return True  # Logo olmadan da çalışabilir

def start_http_server():
    os.chdir(HLS_DIR)
    handler = SimpleHTTPRequestHandler
    
    # Port'u dene, eğer doluysa yenisini bul
    port = PORT
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            server = HTTPServer(("0.0.0.0", port), handler)
            break
        except OSError:
            port += 1
            if attempt == max_attempts - 1:
                print("Port bulunamadı!")
                return
    
    local_ip = get_local_ip()
    print(f"\n📺 Yayın başlatıldı!")
    print(f"📍 Yerel: http://127.0.0.1:{port}/playlist.m3u8")
    print(f"📍 Ağ: http://{local_ip}:{port}/playlist.m3u8")
    print("🛑 Durdurmak için Ctrl+C\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

def main():
    print("🚀 HLS Stream Generator başlatılıyor...")
    
    # Logo'yu indir (başarısız olursa devam et)
    download_logo()
    
    # FFmpeg'in varlığını kontrol et
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg bulunamadı! Lütfen ffmpeg'i yükleyin.")
        sys.exit(1)
    
    # HTTP sunucusunu arka planda başlat
    t = threading.Thread(target=start_http_server, daemon=True)
    t.start()
    time.sleep(2)
    
    print("📡 Yayın başlatılıyor...")
    
    # FFmpeg komutunu oluştur
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "warning",
        "-re",
        "-i", INPUT,
        "-i", str(LOGO_PATH) if LOGO_PATH.exists() else "color=black:s=1x1",
        "-filter_complex", "[0:v][1:v]overlay=W-w-15:15:format=auto,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-b:v", "1100k",
        "-maxrate", "1100k",
        "-bufsize", "2000k",
        "-g", "30",
        "-c:a", "aac",
        "-b:a", "96k",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "6",
        "-hls_flags", "delete_segments+append_list+omit_endlist",
        "-hls_segment_filename", str(HLS_DIR / "seg_%05d.ts"),
        str(HLS_DIR / "playlist.m3u8")
    ]
    
    try:
        print("✅ Yayın akışı başladı!")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️ Yayın durduruldu.")
    except Exception as e:
        print(f"❌ Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
