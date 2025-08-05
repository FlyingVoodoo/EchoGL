from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap 
from PyQt6.QtCore import Qt 

from pathlib import Path
import os 

from core.steam_scanner import find_all_potential_steamapps_folders, parse_acf_file
from core.cover_downloader import CoverDownloader
from data.db_manager import get_db_manager
from utils.metadata_updater import update_all_games_with_metadata

class GameManager(QObject):
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(list) 
    game_launched = pyqtSignal(str) 
    
    request_display_cover = pyqtSignal(str, QObject, str, bool) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = get_db_manager()
        self.covers_dir = Path.home() / ".EchoGL" / "covers" 
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        self.cover_downloader = CoverDownloader(self.covers_dir) 

    def scan_for_games(self):
        self.scan_started.emit()
        print("Games scanning starts...")

        all_steamapps_folders = find_all_potential_steamapps_folders()
        
        found_games_this_scan = []
        for steamapps_folder in all_steamapps_folders:
            acf_files = list(steamapps_folder.glob('appmanifest_*.acf'))
            for acf_file in acf_files:
                game_info = parse_acf_file(acf_file)
                if game_info and 'appid' in game_info and 'name' in game_info:
                    appid = game_info['appid']
                    common_path = steamapps_folder / "common"
                    game_install_path = common_path / game_info.get('installdir', '')
                    if game_install_path.is_dir():
                        game_info['full_install_path'] = str(game_install_path)
                    else:
                        game_info['full_install_path'] = 'N/A - Not Found'

                    thumbnail_path = self.cover_downloader.download_and_save_cover(appid, 'thumbnail')
                    detail_path = self.cover_downloader.download_and_save_cover(appid, 'detail')
                    
                    game_info['cover_thumbnail_path'] = str(thumbnail_path) if thumbnail_path else None
                    game_info['cover_detail_path'] = str(detail_path) if detail_path else None

                    self.db_manager.add_or_update_game(game_info)
                    found_games_this_scan.append(game_info)
        
        all_current_games_from_db = self.db_manager.get_all_games()
        self.scan_finished.emit(all_current_games_from_db)
        print("Scaning is finished.")

        print("Starting updating metadata and covers with IGDB...")
        update_all_games_with_metadata()
        print("Metadate's update is finished")

    def get_all_games(self):
        return self.db_manager.get_all_games()

    def get_game_by_appid(self, appid):
        return self.db_manager.get_game_by_appid(appid)

    def launch_game(self, appid):
        if appid:
            QDesktopServices.openUrl(QUrl(f"steam://rungameid/{appid}"))
            self.game_launched.emit(appid)
            print(f"Игра с AppID {appid} запущена.")
        else:
            print("Не удалось запустить игру: AppID не указан.")

    def display_cover_on_label(self, appid, target_label, cover_type='thumbnail', use_cached=False):
        if not appid:
            target_label.clear()
            target_label.setText("No AppID")
            target_label.setStyleSheet("border: 1px solid red; border-radius: 5px; color: red;")
            return
        
        pixmap_to_display = QPixmap()

        if use_cached:
            game_from_db = self.db_manager.get_game_by_appid(appid)
            if game_from_db:
                local_cover_path = None
                if cover_type == 'thumbnail':
                    local_cover_path = game_from_db.get('cover_thumbnail_path')
                elif cover_type == 'detail':
                    local_cover_path = game_from_db.get('cover_detail_path')

                if local_cover_path and Path(local_cover_path).is_file():
                    try:
                        loaded_pixmap = QPixmap(local_cover_path)
                        if not loaded_pixmap.isNull():
                            pixmap_to_display = loaded_pixmap
                    except Exception as e:
                        print(f"ERROR: Failed to load cached cover for AppID {appid} from {local_cover_path}: {e}")
        
        if pixmap_to_display.isNull():
            downloaded_path = self.cover_downloader.download_and_save_cover(appid, cover_type)
            if downloaded_path and Path(downloaded_path).is_file():
                try:
                    loaded_pixmap = QPixmap(str(downloaded_path))
                    if not loaded_pixmap.isNull():
                        pixmap_to_display = loaded_pixmap
                except Exception as e:
                    print(f"ERROR: Failed to load newly downloaded cover for AppID {appid} from {downloaded_path}: {e}")

        if not pixmap_to_display.isNull():
            if hasattr(target_label, 'setOriginalPixmap') and callable(getattr(target_label, 'setOriginalPixmap')):
                target_label.setOriginalPixmap(pixmap_to_display)
            else:
                scaled_pixmap = pixmap_to_display.scaled(target_label.size(),
                                                         Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                         Qt.TransformationMode.SmoothTransformation)
                target_label.setPixmap(scaled_pixmap)
        else:
            target_label.clear()
            target_label.setText(f"No cover for {appid}")
            target_label.setStyleSheet("border: 1px solid red; border-radius: 5px; color: red;")
            print(f"Failed to load any cover for AppID {appid}.")

    def close_db(self):
        if self.db_manager:
            self.db_manager.close()

import sys
import requests 
from PIL import Image 
from io import BytesIO