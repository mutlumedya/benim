#!/usr/bin/env python3
import subprocess
import requests
import os
from pathlib import Path
import shutil
import time

# ================== AYARLAR ==================
INPUT = os.environ.get('INPUT_URL', 'https://cdn.codenet.lol/streamgo/stremgo123/4866.m3u8')
LOGO_URL = "https://raw.githubusercontent.com/mutlumedya/yay-n-1/refs/heads/main/logo.png"

# GitHub Pages için çıktı dizini
OUTPUT_DIR = Path("./hls_output")  # GitHub Pages'e yüklenecek
TEMP_DIR = Path("./temp_hls")      # Geçici çalışma dizini

# =============================================

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

def download_logo():
    """Logo'yu indir"""
    logo_path = TEMP_DIR / "logo.png"
    try:
        r = requests.get(LOGO_URL, timeout=15)
        r.raise_for_status()
        logo_path.write_bytes(r.content)
        print("✅ Logo indirildi")
        return str(logo_path)
    except Exception as e:
        print(f"⚠️ Logo indirilemedi: {e}")
        return None

def generate_hls():
    """HLS segmentlerini oluştur"""
    logo_path = download_logo()
    
    # FFmpeg komutu
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
    
    # Logo varsa overlay ekle
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
    except subprocess.TimeoutExpired:
        print("⚠️ Zaman aşımı, kısmi dosyalar kullanılacak")
        return True  # Kısmi de olsa devam et
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def deploy_to_pages():
    """Dosyaları GitHub Pages dizinine kopyala"""
    print("📤 GitHub Pages'e yükleniyor...")
    
    # Eski dosyaları temizle (opsiyonel)
    # shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Tüm dosyaları kopyala
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            shutil.copy2(file, OUTPUT_DIR / file.name)
    
    # index.html oluştur (HLS oynatıcı)
    create_index_html()
    
    print(f"✅ Dosyalar {OUTPUT_DIR} dizinine kopyalandı")

def create_index_html():
    """HLS oynatıcı için index.html oluştur"""
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HLS Stream</title>
    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
    <style>
        body { margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { width: 100%; max-width: 800px; }
        .video-js { width: 100%; height: 100%; min-height: 400px; }
        .info { color: #fff; text-align: center; padding: 10px; font-family: Arial; }
        .status { color: #0f0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="info">
            <span class="status">🟢 CANLI YAYIN</span>
        </div>
        <video id="my-video" class="video-js vjs-default-skin" controls autoplay>
            <source src="playlist.m3u8" type="application/x-mpegURL">
        </video>
    </div>
    
    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
    <script>
        var player = videojs('my-video', {
            html5: {
                hls: {
                    enableLowInitialPlaylist: true,
                    smoothQualityChange: true,
                    overrideNative: true
                }
            }
        });
        
        // Hata durumunda yeniden dene
        player.on('error', function() {
            setTimeout(function() {
                player.src({ src: 'playlist.m3u8', type: 'application/x-mpegURL' });
                player.play();
            }, 5000);
        });
    </script>
</body>
</html>
'''
    (OUTPUT_DIR / "index.html").write_text(html_content)
    print("✅ index.html oluşturuldu")

def main():
    print("🚀 HLS Stream Generator başlatıldı...")
    
    # Eski geçici dosyaları temizle
    for file in TEMP_DIR.glob("*"):
        file.unlink()
    
    # HLS oluştur
    success = generate_hls()
    
    # GitHub Pages'e yükle
    deploy_to_pages()
    
    if success:
        print("\n✅ Yayın başarıyla güncellendi!")
        print("🔗 İzlemek için: https://[KULLANICI_ADI].github.io/[REPO_ADI]/")
    else:
        print("\n⚠️ Yayın kısmi olarak güncellendi.")

if __name__ == "__main__":
    main()
