import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import os 

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
            return local_path

        if image_data is None:
            for cover_url in cover_config['urls']:
                try:
                    response = requests.get(cover_url, stream=True, timeout=5)
                    response.raise_for_status()
                    image_data = response.content
                    break
                except requests.exceptions.RequestException:
                    pass
            if image_data is None:
                return None

        try:
            img = Image.open(BytesIO(image_data))
            if cover_config['resize']:
                img = img.resize(cover_config['resize'], Image.LANCZOS)

            img.save(local_path)
        except Exception:
            return None
        return local_path