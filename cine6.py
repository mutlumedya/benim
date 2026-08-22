#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import shutil
import threading
import subprocess
import tempfile
import hashlib
from datetime import datetime

# ============================================================
# RENKLER
# ============================================================

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
RESET = "\033[0m"


def log(color, text):
    print(
        f"{color}[{datetime.now().strftime('%H:%M:%S')}] "
        f"{text}{RESET}",
        flush=True
    )


# ============================================================
# OTOMATİK KURULUM
# ============================================================

def run_command(command):
    try:
        subprocess.run(command, check=True)
        return True
    except Exception:
        return False


def install_dependencies():

    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    log(YELLOW, "FFmpeg bulunamadı. Paket kurulumu başlıyor...")

    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        log(RED, "FFmpeg kurulumu için root yetkisi gerekiyor.")
        log(YELLOW, "Şöyle çalıştır:")
        print("sudo python3 yayin.py")
        sys.exit(1)

    run_command(["apt-get", "update"])

    packages = [
        "ffmpeg",
        "python3",
        "python3-pip",
        "python3-requests",
        "ca-certificates"
    ]

    if not run_command(
        ["apt-get", "install", "-y"] + packages
    ):
        log(RED, "Gerekli paketler kurulamadı.")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        log(RED, "FFmpeg hala bulunamıyor.")
        sys.exit(1)

    if not shutil.which("ffprobe"):
        log(RED, "FFprobe hala bulunamıyor.")
        sys.exit(1)


install_dependencies()

try:
    import requests
except ImportError:

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            "requests",
            "--break-system-packages"
        ])
    else:
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            "requests"
        ])

    import requests


# ============================================================
# GENEL AYARLAR
# ============================================================

CHECK_INTERVAL = 300
RESTART_DELAY = 5
CHANNEL_START_DELAY = 3

# 03:00 - 04:00 arasında yayın yok
NIGHT_START = 3
NIGHT_END = 4

# Film arası
AD_INTERVAL = 30 * 60

# Reklam süresi
AD_DURATION = 5 * 60

# Reklamdan önce/sonra kart süresi
CARD_DURATION = 5

# Video
WIDTH = 1280
HEIGHT = 720

VIDEO_BITRATE = "2000k"
MAXRATE = "2000k"
BUFSIZE = "4000k"

AUDIO_BITRATE = "96k"
AUDIO_RATE = "44100"

LOGO_WIDTH = 150


# ============================================================
# RTMP
#
# BURAYA KENDİ/YETKİLİ RTMP BİLGİNİ KOY
# ============================================================

RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101"



# ============================================================
# 6 KANAL
#
# Her kanalın:
# - ayrı GitHub M3U'su
# - ayrı yayın key'i
# - ayrı logosu
# - ayrı reklam listesi
# ============================================================

CHANNELS = [

    {
        "name": "YAYIN 1",
        "key": "zemtv",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/logo.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam1.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam2.mp4",
        ]
    },

    {
        "name": "YAYIN 2",
        "key": "zemtvaile",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/zemtvaile.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam3.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam4.mp4",
        ]
    },

    {
        "name": "YAYIN 3",
        "key": "zemtvcocuk",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/zemtvcocuk.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam5.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam6.mp4",
        ]
    },

    {
        "name": "YAYIN 4",
        "key": "zemtvaksiyon",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/zemtvaksiyon.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam7.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam8.mp4",
        ]
    },

    {
        "name": "YAYIN 5",
        "key": "zemtvspor",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/zemtvspor.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam9.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam10.mp4",
        ]
    },

    {
        "name": "YAYIN 6",
        "key": "zemtvbelgesel",
        "m3u": "https://raw.githubusercontent.com/mutlumedya/yayin2/refs/heads/main/action.m3u",
        "logo": "https://raw.githubusercontent.com/mutlumedya/benim/refs/heads/main/zemtvbelgesel.png",

        "ads": [
            "https://YOUR-AUTHORIZED-SERVER.example/reklam11.mp4",
            "https://YOUR-AUTHORIZED-SERVER.example/reklam12.mp4",
        ]
    }

]


# ============================================================
# GLOBAL
# ============================================================

STOP_EVENT = threading.Event()

PROCESSES = {}
PROCESS_LOCK = threading.Lock()

# Logo cache
LOGO_CACHE = {}


# ============================================================
# RTMP
# ============================================================

def get_output(channel):
    return f"{RTMP_URL}/{channel['key']}"


# ============================================================
# SAAT
# ============================================================

def broadcasting_allowed():

    hour = datetime.now().hour

    return not (
        NIGHT_START <= hour < NIGHT_END
    )


# ============================================================
# M3U İNDİR
# ============================================================

def download_m3u(url):

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return response.text


# ============================================================
# M3U PARSE
# ============================================================

def parse_m3u(content):

    lines = [
        x.strip()
        for x in content.splitlines()
        if x.strip()
    ]

    result = []

    title = None

    for line in lines:

        if line.startswith("#EXTINF"):

            if "," in line:
                title = line.split(",", 1)[1].strip()
            else:
                title = "Film"

            continue

        if line.startswith("#"):
            continue

        if (
            line.startswith("http://")
            or line.startswith("https://")
        ):

            result.append({
                "title": title or "Film",
                "url": line
            })

            title = None

    return result


# ============================================================
# FİLM SÜRESİ
# ============================================================

def get_duration(url):

    try:

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=90
        )

        value = result.stdout.strip()

        if not value:
            return None

        duration = float(value)

        if duration <= 0:
            return None

        return duration

    except Exception as e:

        log(
            RED,
            f"FFprobe hata: {e}"
        )

        return None


# ============================================================
# PROCESS
# ============================================================

def set_process(name, process):

    with PROCESS_LOCK:
        PROCESSES[name] = process


def remove_process(name):

    with PROCESS_LOCK:
        PROCESSES.pop(name, None)


def stop_process(name):

    with PROCESS_LOCK:

        process = PROCESSES.get(name)

        if not process:
            return

        try:

            if process.poll() is None:

                process.terminate()

                try:
                    process.wait(timeout=5)

                except subprocess.TimeoutExpired:

                    process.kill()
                    process.wait()

        except Exception:
            pass

        PROCESSES.pop(name, None)


def stop_all():

    with PROCESS_LOCK:

        names = list(PROCESSES.keys())

    for name in names:
        stop_process(name)


# ============================================================
# LOGO - URL'DEN İNDİR
# ============================================================

def get_logo_path(channel):
    """
    Logo URL'sini indir ve yerel dosya yolunu döndür.
    Eğer logo yoksa veya indirilemezse None döndür.
    """
    logo_url = channel.get("logo")
    
    if not logo_url:
        return None
    
    # Eğer zaten yerel dosya ise kontrol et
    if not logo_url.startswith(("http://", "https://")):
        if os.path.isfile(logo_url):
            return logo_url
        return None
    
    # Cache'ten kontrol et
    if logo_url in LOGO_CACHE:
        cached_path = LOGO_CACHE[logo_url]
        if os.path.isfile(cached_path):
            return cached_path
        else:
            # Cache'teki dosya silinmiş, tekrar indir
            del LOGO_CACHE[logo_url]
    
    # URL'den indir
    try:
        # Benzersiz dosya adı oluştur
        url_hash = hashlib.md5(logo_url.encode()).hexdigest()
        local_path = os.path.join(tempfile.gettempdir(), f"logo_{url_hash}.png")
        
        # İndir
        response = requests.get(logo_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0"
        })
        response.raise_for_status()
        
        # İçeriğin resim olduğunu kontrol et
        content_type = response.headers.get('content-type', '').lower()
        if 'image' not in content_type and 'png' not in content_type:
            log(YELLOW, f"[{channel['name']}] Logo URL'si resim değil: {logo_url} (Content-Type: {content_type})")
            return None
        
        # Dosyaya yaz
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        # Cache'e ekle
        LOGO_CACHE[logo_url] = local_path
        
        log(GREEN, f"[{channel['name']}] Logo indirildi: {local_path}")
        return local_path
        
    except Exception as e:
        log(RED, f"[{channel['name']}] Logo indirilemedi: {logo_url} - {e}")
        return None


def has_logo(channel):
    """Logo varsa ve erişilebilir durumdaysa True döndür"""
    logo_path = get_logo_path(channel)
    return bool(logo_path and os.path.isfile(logo_path))


# ============================================================
# TITLE ESCAPE
# ============================================================

def escape_drawtext(text):

    text = str(text)

    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    text = text.replace("%", "\\%")

    return text


# ============================================================
# NORMAL VİDEO FİLTRESİ
# ============================================================

def video_filter(channel):

    logo_path = get_logo_path(channel)

    if logo_path and os.path.isfile(logo_path):

        return (
            f"[0:v]"
            f"scale={WIDTH}:{HEIGHT}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:"
            f"(ow-iw)/2:(oh-ih)/2:black"
            f"[base];"

            f"[1:v]"
            f"scale={LOGO_WIDTH}:-1"
            f"[logo];"

            f"[base][logo]"
            f"overlay=W-w-15:15"
            f"[v]"
        )

    return (
        f"[0:v]"
        f"scale={WIDTH}:{HEIGHT}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:"
        f"(ow-iw)/2:(oh-ih)/2:black"
        f"[v]"
    )


# ============================================================
# NORMAL FİLM / REKLAM OYNAT
# ============================================================

def play_media(
    channel,
    source,
    duration,
    seek=0,
    media_type="film"
):

    name = channel["name"]

    output = get_output(channel)

    logo_path = get_logo_path(channel)

    try:

        if logo_path and os.path.isfile(logo_path):

            filter_complex = video_filter(channel)

            command = [

                "ffmpeg",

                "-hide_banner",
                "-loglevel",
                "error",

                "-ss",
                str(seek),

                "-t",
                str(duration),

                "-i",
                source,

                "-loop",
                "1",

                "-i",
                logo_path,

                "-filter_complex",
                filter_complex,

                "-map",
                "[v]",

                "-map",
                "0:a?",

                "-c:v",
                "libx264",

                "-preset",
                "ultrafast",

                "-tune",
                "zerolatency",

                "-pix_fmt",
                "yuv420p",

                "-b:v",
                VIDEO_BITRATE,

                "-maxrate",
                MAXRATE,

                "-bufsize",
                BUFSIZE,

                "-g",
                "120",

                "-c:a",
                "aac",

                "-b:a",
                AUDIO_BITRATE,

                "-ar",
                AUDIO_RATE,

                "-threads",
                "1",

                "-f",
                "flv",

                output
            ]

        else:

            command = [

                "ffmpeg",

                "-hide_banner",
                "-loglevel",
                "error",

                "-ss",
                str(seek),

                "-t",
                str(duration),

                "-i",
                source,

                "-vf",

                (
                    f"scale={WIDTH}:{HEIGHT}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={WIDTH}:{HEIGHT}:"
                    f"(ow-iw)/2:(oh-ih)/2:black"
                ),

                "-map",
                "0:v:0",

                "-map",
                "0:a?",

                "-c:v",
                "libx264",

                "-preset",
                "ultrafast",

                "-tune",
                "zerolatency",

                "-pix_fmt",
                "yuv420p",

                "-b:v",
                VIDEO_BITRATE,

                "-maxrate",
                MAXRATE,

                "-bufsize",
                BUFSIZE,

                "-g",
                "120",

                "-c:a",
                "aac",

                "-b:a",
                AUDIO_BITRATE,

                "-ar",
                AUDIO_RATE,

                "-threads",
                "1",

                "-f",
                "flv",

                output
            ]

        log(
            CYAN,
            f"[{name}] {media_type.upper()} oynatılıyor..."
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        set_process(name, process)

        while True:

            if STOP_EVENT.is_set():
                stop_process(name)
                return False

            if not broadcasting_allowed():
                stop_process(name)
                return False

            code = process.poll()

            if code is not None:

                remove_process(name)

                return code == 0

            time.sleep(1)

    except Exception as e:

        log(
            RED,
            f"[{name}] FFmpeg hata: {e}"
        )

        stop_process(name)

        return False


# ============================================================
# KART OYNAT
#
# Reklam öncesi:
# "FİLM ADI - REKLAMLARDAN SONRA DEVAM EDECEK"
#
# Reklam sonrası:
# "FİLM ADI - DEVAM EDİYOR"
# ============================================================

def play_card(
    channel,
    title,
    message
):

    name = channel["name"]

    output = get_output(channel)

    text = escape_drawtext(
        f"{title} - {message}"
    )

    logo_path = get_logo_path(channel)

    try:

        # ----------------------------------------------------
        # LOGOLU KART
        # ----------------------------------------------------

        if logo_path and os.path.isfile(logo_path):

            filter_complex = (

                f"[1:v]"
                f"scale={LOGO_WIDTH}:-1"
                f"[logo];"

                f"[0:v]"
                f"drawtext="
                f"text='{text}':"
                f"fontcolor=white:"
                f"fontsize=38:"
                f"borderw=3:"
                f"bordercolor=black:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2"
                f"[card];"

                f"[card][logo]"
                f"overlay=W-w-15:15"
                f"[v]"
            )

            command = [

                "ffmpeg",

                "-hide_banner",
                "-loglevel",
                "error",

                "-f",
                "lavfi",

                "-i",
                (
                    f"color=c=black:"
                    f"s={WIDTH}x{HEIGHT}:"
                    f"r=25"
                ),

                "-loop",
                "1",

                "-i",
                logo_path,

                "-filter_complex",
                filter_complex,

                "-map",
                "[v]",

                "-f",
                "lavfi",

                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",

                "-map",
                "2:a",

                "-t",
                str(CARD_DURATION),

                "-c:v",
                "libx264",

                "-preset",
                "ultrafast",

                "-tune",
                "zerolatency",

                "-pix_fmt",
                "yuv420p",

                "-b:v",
                "1000k",

                "-c:a",
                "aac",

                "-b:a",
                "96k",

                "-shortest",

                "-f",
                "flv",

                output
            ]

        # ----------------------------------------------------
        # LOGOSUZ KART
        # ----------------------------------------------------

        else:

            vf = (
                f"drawtext="
                f"text='{text}':"
                f"fontcolor=white:"
                f"fontsize=38:"
                f"borderw=3:"
                f"bordercolor=black:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2"
            )

            command = [

                "ffmpeg",

                "-hide_banner",
                "-loglevel",
                "error",

                "-f",
                "lavfi",

                "-i",
                (
                    f"color=c=black:"
                    f"s={WIDTH}x{HEIGHT}:"
                    f"r=25"
                ),

                "-f",
                "lavfi",

                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",

                "-vf",
                vf,

                "-map",
                "0:v",

                "-map",
                "1:a",

                "-t",
                str(CARD_DURATION),

                "-c:v",
                "libx264",

                "-preset",
                "ultrafast",

                "-tune",
                "zerolatency",

                "-pix_fmt",
                "yuv420p",

                "-b:v",
                "1000k",

                "-c:a",
                "aac",

                "-b:a",
                "96k",

                "-shortest",

                "-f",
                "flv",

                output
            ]

        log(
            MAGENTA,
            f"[{name}] KART → {title} / {message}"
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        set_process(name, process)

        while True:

            if STOP_EVENT.is_set():
                stop_process(name)
                return False

            if not broadcasting_allowed():
                stop_process(name)
                return False

            code = process.poll()

            if code is not None:

                remove_process(name)

                return code == 0

            time.sleep(1)

    except Exception as e:

        log(
            RED,
            f"[{name}] Kart hatası: {e}"
        )

        stop_process(name)

        return False


# ============================================================
# REKLAM SEÇ
# ============================================================

def get_ad(channel, index):

    ads = channel.get("ads", [])

    if not ads:
        return None

    return ads[
        index % len(ads)
    ]


# ============================================================
# FİLM OYNATMA
# ============================================================

def play_movie(
    channel,
    movie,
    ad_index
):

    name = channel["name"]

    title = movie["title"]

    url = movie["url"]

    log(
        GREEN,
        f"[{name}] 🎬 {title}"
    )

    # --------------------------------------------------------
    # FİLMİN GERÇEK SÜRESİ
    # --------------------------------------------------------

    duration = get_duration(url)

    if duration is None:

        log(
            RED,
            f"[{name}] Film süresi okunamadı: {title}"
        )

        return False, ad_index

    log(
        BLUE,
        f"[{name}] Süre: "
        f"{duration / 60:.2f} dakika"
    )

    position = 0.0

    # --------------------------------------------------------
    # 30 DAKİKALIK BÖLÜMLER
    # --------------------------------------------------------

    while position < duration:

        remaining = duration - position

        segment = min(
            AD_INTERVAL,
            remaining
        )

        # ----------------------------------------------------
        # FİLM
        # ----------------------------------------------------

        ok = play_media(
            channel,
            url,
            segment,
            position,
            "film"
        )

        if not ok:

            if not broadcasting_allowed():
                return False, ad_index

            time.sleep(
                RESTART_DELAY
            )

            continue

        position += segment

        # ----------------------------------------------------
        # FİLM BİTMEDİYSE REKLAM
        # ----------------------------------------------------

        if position < duration:

            ad = get_ad(
                channel,
                ad_index
            )

            ad_index += 1

            if ad:

                # --------------------------------------------
                # REKLAMDAN ÖNCE KART
                # --------------------------------------------

                play_card(
                    channel,
                    title,
                    "Reklamlardan sonra devam edecek"
                )

                # --------------------------------------------
                # REKLAM
                # --------------------------------------------

                log(
                    YELLOW,
                    f"[{name}] 📢 REKLAM"
                )

                ad_ok = play_media(
                    channel,
                    ad,
                    AD_DURATION,
                    0,
                    "reklam"
                )

                if not ad_ok:
                    time.sleep(RESTART_DELAY)

                # --------------------------------------------
                # REKLAMDAN SONRA KART
                # --------------------------------------------

                play_card(
                    channel,
                    title,
                    "Devam ediyor"
                )

            else:

                log(
                    YELLOW,
                    f"[{name}] Reklam tanımlı değil."
                )

    # --------------------------------------------------------
    # FİLM BİTTİ
    # --------------------------------------------------------

    log(
        GREEN,
        f"[{name}] ✓ {title} sona erdi."
    )

    # --------------------------------------------------------
    # FİLM SONU REKLAMI
    # --------------------------------------------------------

    ad = get_ad(
        channel,
        ad_index
    )

    ad_index += 1

    if ad:

        play_card(
            channel,
            title,
            "Film sona erdi"
        )

        log(
            YELLOW,
            f"[{name}] 📢 Film sonu reklamı"
        )

        play_media(
            channel,
            ad,
            AD_DURATION,
            0,
            "reklam"
        )

    return True, ad_index


# ============================================================
# KANAL ÇALIŞTIRICI
# ============================================================

def channel_worker(channel):

    name = channel["name"]

    log(
        GREEN,
        f"[{name}] Scheduler başlatıldı."
    )

    # Logoyu önceden indir
    get_logo_path(channel)

    ad_index = 0

    while not STOP_EVENT.is_set():

        # ----------------------------------------------------
        # GECE
        # ----------------------------------------------------

        if not broadcasting_allowed():

            stop_process(name)

            time.sleep(20)

            continue

        # ----------------------------------------------------
        # GITHUB M3U
        # ----------------------------------------------------

        try:

            content = download_m3u(
                channel["m3u"]
            )

            playlist = parse_m3u(
                content
            )

        except Exception as e:

            log(
                RED,
                f"[{name}] M3U okunamadı: {e}"
            )

            time.sleep(30)

            continue

        if not playlist:

            log(
                RED,
                f"[{name}] M3U boş."
            )

            time.sleep(30)

            continue

        log(
            GREEN,
            f"[{name}] {len(playlist)} film bulundu."
        )

        # ----------------------------------------------------
        # FILMLER
        # ----------------------------------------------------

        for movie in playlist:

            if STOP_EVENT.is_set():
                break

            if not broadcasting_allowed():
                break

            success, ad_index = play_movie(
                channel,
                movie,
                ad_index
            )

            if not success:

                if not broadcasting_allowed():
                    break

                time.sleep(
                    RESTART_DELAY
                )

        # ----------------------------------------------------
        # PLAYLIST BİTTİ
        # ----------------------------------------------------

        if broadcasting_allowed():

            log(
                BLUE,
                f"[{name}] Playlist bitti."
            )

            # Yeni listeyi almadan önce kısa bekleme
            time.sleep(5)


# ============================================================
# GECE KONTROL
# ============================================================

def night_controller():

    stopped = False

    while not STOP_EVENT.is_set():

        hour = datetime.now().hour

        # ----------------------------------------------------
        # 03:00
        # ----------------------------------------------------

        if hour == NIGHT_START:

            if not stopped:

                log(
                    YELLOW,
                    "🌙 03:00 → TÜM YAYINLAR KAPATILIYOR"
                )

                stop_all()

                stopped = True

        # ----------------------------------------------------
        # 04:00
        # ----------------------------------------------------

        elif hour == NIGHT_END:

            if stopped:

                log(
                    GREEN,
                    "☀ 04:00 → YAYINLAR YENİDEN BAŞLIYOR"
                )

                stopped = False

        time.sleep(10)


# ============================================================
# KAPATMA
# ============================================================

def shutdown():

    if STOP_EVENT.is_set():
        return

    log(
        RED,
        "Sistem kapatılıyor..."
    )

    STOP_EVENT.set()

    stop_all()

    log(
        GREEN,
        "✓ Tüm FFmpeg süreçleri kapatıldı."
    )


def signal_handler(
    signum,
    frame
):

    shutdown()

    sys.exit(0)


# ============================================================
# BAŞLANGIÇ
# ============================================================

def main():

    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    signal.signal(
        signal.SIGTERM,
        signal_handler
    )

    log(BLUE, "")
    log(BLUE, "=" * 70)
    log(GREEN, "       6 KANALLI TV PLAYOUT SİSTEMİ")
    log(BLUE, "=" * 70)

    log(
        GREEN,
        "✓ FFmpeg hazır"
    )

    log(
        GREEN,
        "✓ FFprobe hazır"
    )

    log(
        GREEN,
        "✓ GitHub M3U sistemi hazır"
    )

    log(
        GREEN,
        "✓ Otomatik film süresi"
    )

    log(
        GREEN,
        "✓ 30 dakika reklam aralığı"
    )

    log(
        GREEN,
        "✓ Film sonu reklam"
    )

    log(
        GREEN,
        "✓ Kanal başına ayrı reklam havuzu"
    )

    log(
        GREEN,
        "✓ Reklam öncesi kart"
    )

    log(
        GREEN,
        "✓ Reklam sonrası kart"
    )

    log(
        GREEN,
        "✓ Kanal başına ayrı logo (URL'den indirilir)"
    )

    log(
        GREEN,
        "✓ 03:00 - 04:00 yayın molası"
    )

    log(BLUE, "=" * 70)

    # --------------------------------------------------------
    # Logoları önceden indir (cache'le)
    # --------------------------------------------------------

    log(YELLOW, "Logolar indiriliyor...")
    for channel in CHANNELS:
        logo_path = get_logo_path(channel)
        if logo_path:
            log(GREEN, f"✓ {channel['name']} logosu hazır: {os.path.basename(logo_path)}")
        else:
            log(YELLOW, f"⚠ {channel['name']} logosu yok veya indirilemedi")

    log(BLUE, "=" * 70)

    # --------------------------------------------------------
    # GECE THREAD
    # --------------------------------------------------------

    threading.Thread(
        target=night_controller,
        daemon=True
    ).start()

    # --------------------------------------------------------
    # 6 KANAL
    # --------------------------------------------------------

    for channel in CHANNELS:

        threading.Thread(
            target=channel_worker,
            args=(channel,),
            daemon=True
        ).start()

        log(
            GREEN,
            f"✓ {channel['name']} aktif"
        )

        time.sleep(
            CHANNEL_START_DELAY
        )

    log(BLUE, "")
    log(BLUE, "=" * 70)
    log(GREEN, "             SİSTEM AKTİF")
    log(BLUE, "=" * 70)

    try:

        while not STOP_EVENT.is_set():
            time.sleep(30)

    except KeyboardInterrupt:

        shutdown()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
