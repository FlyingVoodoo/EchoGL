import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import os 
import time

class CoverDownloader:
    def __init__(self, base_covers_dir=None):
        if base_covers_dir:
            self.covers_dir = Path(base_covers_dir)
        else:
            self.covers_dir = Path.home() / ".EchoGL" / "covers"
        self.covers_dir.mkdir(parents=True, exist_ok=True)

    def download_and_save_cover(self, appid, cover_type, image_data=None):
        cover_urls_map = {
            'thumbnail': {
                'urls': [
                    f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                    f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_231x87.jpg",
                ],
                'filename': f"{appid}_thumbnail.jpg",
                'resize': (180, 270)
            },
            'detail': {
                'urls': [
                    f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_hero.jpg",
                    f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
                ],
                'filename': f"{appid}_detail.jpg",
                'resize': None
            }
        }

        cover_config = cover_urls_map.get(cover_type)
        if not cover_config:
            return None

        local_path = self.covers_dir / cover_config['filename']

        if local_path.is_file():
            return str(local_path)

        if image_data is None:
            max_retries = 3
            for attempt in range(max_retries):
                for cover_url in cover_config['urls']:
                    try:
                        response = requests.get(cover_url, stream=True, timeout=60)
                        response.raise_for_status()
                        image_data = response.content
                        break
                    except requests.exceptions.RequestException:
                        pass
                if image_data:
                    break
                print(f"Failed to get Steam cover on attempt {attempt+1}/{max_retries}, retrying...")
                time.sleep(5)
            if image_data is None:
                return None

        try:
            img = Image.open(BytesIO(image_data))
            if cover_config['resize']:
                img = img.resize(cover_config['resize'], Image.LANCZOS)

            img.save(local_path)
        except Exception:
            return None
        return str(local_path)
    
    def download_igdb_cover(self, igdb_url, game_name):
        if not igdb_url:
            return None
        
        igdb_covers_dir = self.covers_dir / "igdb"
        igdb_covers_dir.mkdir(parents=True, exist_ok=True)

        full_url = f"https:{igdb_url}"

        safe_game_name = "".join(c for c in game_name if c.isalnum() or c in (' ',)).rstrip()
        filename = f"{safe_game_name.replace(' ', '_').lower()}.jpg"

        local_path = igdb_covers_dir / filename

        if local_path.is_file():
            return str(local_path)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to download cover from URL: {full_url} (Attempt {attempt+1}/{max_retries})")
                response = requests.get(full_url, stream=True, timeout=60)
                response.raise_for_status()

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"Successfully downloaded cover for '{game_name}'")
                return str(local_path)
            
            except requests.exceptions.RequestException as e:
                print(f"Error downloading IGDB cover for '{game_name}': {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"Failed to download cover for '{game_name}' after {max_retries} attempts.")
                    return None