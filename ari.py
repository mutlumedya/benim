#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arı Maya - M3U Oluşturucu
Tüm bölümleri Sibnet API'den çeker ve M3U dosyası olarak kaydeder.
Her 2 saatte bir otomatik yenilenir.
"""

import os
import re
import json
import time
import schedule
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================
# KONFIGÜRASYON
# ============================================

CONFIG = {
    "anime_name": "Arı Maya",
    "anime_slug": "ari-maya",
    "seasons": {
        "1": {"episodes": 100, "start_id": 4833414},
        "2": {"episodes": 26, "start_id": 4833514},
        "3": {"episodes": 26, "start_id": 4833614},
        "4": {"episodes": 52, "start_id": 4833714},
    },
    "output_dir": "./m3u_output",
    "m3u_file": "ari_maya.m3u",
    "yml_file": "ari_maya_update.yml",
    "sibnet_base": "https://video.sibnet.ru/shell.php?videoid=",
    "stream_proxy": "https://stream.cizgimax.online/embed/",  # Alternatif proxy
}

# ============================================
# M3U OLUŞTURUCU
# ============================================

class M3UGenerator:
    def __init__(self, config):
        self.config = config
        self.episodes = []
        self.output_path = os.path.join(config["output_dir"], config["m3u_file"])
        self.yml_path = os.path.join(config["output_dir"], config["yml_file"])
        
        # Dizin oluştur
        os.makedirs(config["output_dir"], exist_ok=True)
    
    def fetch_sibnet_episode(self, video_id):
        """Sibnet'ten video bilgilerini çek"""
        url = f"{self.config['sibnet_base']}{video_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Sayfadan başlık ve bilgileri çek
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else f"Bölüm {video_id}"
                return {
                    "id": video_id,
                    "title": title.strip(),
                    "url": url,
                    "proxy_url": f"{self.config['stream_proxy']}{video_id}",
                    "status": "ok"
                }
        except Exception as e:
            print(f"❌ Video {video_id} alınamadı: {e}")
            return {
                "id": video_id,
                "title": f"Bölüm {video_id} (hata)",
                "url": url,
                "proxy_url": f"{self.config['stream_proxy']}{video_id}",
                "status": "error"
            }
        return None
    
    def generate_episodes(self):
        """Tüm bölümleri oluştur"""
        print(f"🔄 {self.config['anime_name']} bölümleri toplanıyor...")
        self.episodes = []
        
        for season, data in self.config["seasons"].items():
            count = data["episodes"]
            start_id = data["start_id"]
            
            for i in range(count):
                video_id = start_id + i
                ep_num = i + 1
                
                # Önce proxy üzerinden dene, sonra direkt Sibnet
                ep = self.fetch_sibnet_episode(video_id)
                if ep:
                    ep["season"] = int(season)
                    ep["episode"] = ep_num
                    self.episodes.append(ep)
                    
                    # İlerleme göster
                    if ep_num % 10 == 0:
                        print(f"  ⏳ Sezon {season}: {ep_num}/{count} bölüm işlendi")
        
        print(f"✅ Toplam {len(self.episodes)} bölüm toplandı!")
        return self.episodes
    
    def create_m3u(self):
        """M3U dosyasını oluştur"""
        if not self.episodes:
            print("❌ Hiç bölüm yok! Önce generate_episodes() çalıştır.")
            return
        
        # M3U başlığı
        m3u_content = [
            "#EXTM3U",
            f'#PLAYLIST: {self.config["anime_name"]} - Tüm Bölümler',
            f'#GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'#URL: https://cizgimax.online/diziler/{self.config["anime_slug"]}-izle/',
            "",
        ]
        
        # Her bölüm için M3U entry'si
        for ep in self.episodes:
            season = ep["season"]
            episode = ep["episode"]
            title = f"{self.config['anime_name']} S{season:02d}E{episode:02d}"
            video_id = ep["id"]
            
            # Ana link (Sibnet)
            m3u_content.append(f'#EXTINF:-1,{title}')
            m3u_content.append(ep["url"])
            
            # Proxy link (alternatif)
            m3u_content.append(f'#EXTINF:-1,{title} (Proxy)')
            m3u_content.append(ep["proxy_url"])
            
            m3u_content.append("")  # Boş satır
        
        # Dosyaya yaz
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_content))
        
        print(f"✅ M3U dosyası oluşturuldu: {self.output_path}")
        print(f"📊 Toplam {len(self.episodes)} bölüm eklendi.")
        return self.output_path
    
    def create_yml(self):
        """YAML güncelleme dosyasını oluştur (her 2 saatte bir yenilenir)"""
        yml_content = {
            "version": "1.0",
            "anime": {
                "name": self.config["anime_name"],
                "slug": self.config["anime_slug"],
                "url": f"https://cizgimax.online/diziler/{self.config['anime_slug']}-izle/",
            },
            "update": {
                "interval": "2h",
                "last_update": datetime.now().isoformat(),
                "next_update": (datetime.now() + timedelta(hours=2)).isoformat(),
            },
            "seasons": self.config["seasons"],
            "episodes": self.episodes,
            "m3u_file": self.config["m3u_file"],
            "total_episodes": len(self.episodes),
        }
        
        with open(self.yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yml_content, f, allow_unicode=True, sort_keys=False)
        
        print(f"✅ YAML dosyası oluşturuldu: {self.yml_path}")
        return self.yml_path

# ============================================
# GÜNCELLEYİCİ (Scheduler)
# ============================================

from datetime import timedelta
import yaml

class M3UUpdater:
    def __init__(self, config):
        self.config = config
        self.generator = M3UGenerator(config)
        self.last_run = None
    
    def run_update(self):
        """Tam güncelleme çalıştır"""
        print(f"\n{'='*50}")
        print(f"🔄 GÜNCELLEME BAŞLADI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        start_time = time.time()
        
        # Bölümleri topla
        self.generator.generate_episodes()
        
        # M3U ve YAML oluştur
        self.generator.create_m3u()
        self.generator.create_yml()
        
        elapsed = time.time() - start_time
        self.last_run = datetime.now()
        
        print(f"⏱️  Süre: {elapsed:.2f} saniye")
        print(f"✅ GÜNCELLEME TAMAMLANDI: {self.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        return True
    
    def schedule_updates(self):
        """Her 2 saatte bir güncelleme planla"""
        # İlk çalıştırma
        self.run_update()
        
        # Her 2 saatte bir (120 dakika)
        schedule.every(2).hours.do(self.run_update)
        
        print("⏰ Zamanlayıcı başlatıldı. Her 2 saatte bir güncelleme yapılacak.")
        print("   Devam etmek için Ctrl+C'ye basın.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Her dakika kontrol et
        except KeyboardInterrupt:
            print("\n⏹️  Zamanlayıcı durduruldu.")

# ============================================
# TEK SEFERLİK ÇALIŞTIRMA (Test)
# ============================================

def run_once():
    """Tek seferlik M3U oluştur"""
    generator = M3UGenerator(CONFIG)
    generator.generate_episodes()
    generator.create_m3u()
    generator.create_yml()
    print("\n✅ Tek seferlik işlem tamamlandı!")

# ============================================
# ANA PROGRAM
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Arı Maya M3U Oluşturucu")
    parser.add_argument("--once", action="store_true", help="Tek seferlik çalıştır")
    parser.add_argument("--schedule", action="store_true", help="Her 2 saatte bir güncelle")
    parser.add_argument("--force", action="store_true", help="Zorla güncelle")
    
    args = parser.parse_args()
    
    if args.force or args.once:
        run_once()
    elif args.schedule:
        updater = M3UUpdater(CONFIG)
        updater.schedule_updates()
    else:
        # Varsayılan: tek seferlik çalıştır
        run_once()
