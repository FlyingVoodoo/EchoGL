import sys
import requests
from PIL import Image
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel,
    QScrollArea, QHBoxLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QUrl, QEvent
from PyQt6.QtGui import QDesktopServices, QPixmap, QMouseEvent

from pathlib import Path

from parser import find_all_potential_steamapps_folders, parse_acf_file

class GameLauncherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Game Launcher")
        self.setGeometry(100, 100, 800, 600)

        style_file = Path(__file__).parent.parent / "style.qss"
        if style_file.exists():
            with open(style_file, "r") as f:
                self.setStyleSheet(f.read())
            print("Successfully loaded style.qss")
        else:
            print(f"Warning: style.qss not found at {style_file}")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.scan_button = QPushButton("Scan Steam Games")
        self.scan_button.clicked.connect(self.scan_games)
        self.main_layout.addWidget(self.scan_button)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.game_list_page = QWidget()
        self.game_list_page_layout = QVBoxLayout(self.game_list_page)
        self.stacked_widget.addWidget(self.game_list_page)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content_widget)
        self.game_list_page_layout.addWidget(self.scroll_area)

        self.scroll_area.viewport().installEventFilter(self)

        self.game_details_page = QWidget()
        self.game_details_layout = QVBoxLayout(self.game_details_page)

        self.detail_cover_label = QLabel()
        self.detail_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_cover_label.setFixedSize(800, 300)
        self.detail_cover_label.setStyleSheet("border: 1px solid gray;")
        
        self.detail_game_name_label = QLabel("Game Name")
        self.detail_game_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.detail_launch_button = QPushButton("Launch Game")
        self.detail_launch_button.clicked.connect(self.launch_game_from_details)
        
        self.detail_info_label = QLabel("Additional info here (ML, stats, description...)")
        self.detail_info_label.setWordWrap(True)

        self.game_details_layout.addWidget(self.detail_cover_label)
        self.game_details_layout.addWidget(self.detail_game_name_label)
        self.game_details_layout.addWidget(self.detail_launch_button)
        self.game_details_layout.addWidget(self.detail_info_label)
        self.game_details_layout.addStretch()

        self.stacked_widget.addWidget(self.game_details_page)

        self.stacked_widget.setCurrentWidget(self.game_list_page)

        self.selected_game_info = None

        self.back_button = QPushButton("Back to Games List")
        self.back_button.clicked.connect(self.go_back_to_game_list)
        self.back_button.hide()
        self.main_layout.addWidget(self.back_button)


    def scan_games(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.selected_game_info = None

        print("Scanning for Steam games...")
        all_steamapps_folders = find_all_potential_steamapps_folders()
        
        found_games = []
        for steamapps_folder in all_steamapps_folders:
            acf_files = list(steamapps_folder.glob('appmanifest_*.acf'))
            for acf_file in acf_files:
                game_info = parse_acf_file(acf_file)
                if game_info and 'appid' in game_info and 'name' in game_info:
                    common_path = steamapps_folder / "common"
                    game_install_path = common_path / game_info.get('installdir', '')
                    if game_install_path.is_dir():
                        game_info['full_install_path'] = str(game_install_path)
                    else:
                        game_info['full_install_path'] = 'N/A - Not Found'

                    found_games.append(game_info)
                    
        if not found_games:
            no_games_label = QLabel("No Steam games found.")
            no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_games_label)
            print("No Steam games found.")
            return
        
        for game in found_games:
            cover_label = QLabel()
            cover_label.setFixedSize(180, 270)
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cover_label.setStyleSheet("border: 1px solid #5a5a5a; border-radius: 5px;")
            cover_label.setCursor(Qt.CursorShape.PointingHandCursor)

            cover_label.setProperty("game_info", game)

            cover_label.installEventFilter(self)

            self.scroll_layout.addWidget(cover_label)
            self.display_cover_on_label(game.get('appid'), cover_label, cover_type='thumbnail')

        self.scroll_layout.addStretch()
        print(f"Found {len(found_games)} Steam games.")

    def display_cover_on_label(self, appid, target_label, cover_type='thumbnail'):
        if not appid:
            target_label.clear()
            target_label.setText("No AppID")
            return

        if cover_type == 'thumbnail':
            cover_urls_to_try = [
                f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_231x87.jpg",
                f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
            ]
        elif cover_type == 'detail':
            cover_urls_to_try = [
                f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_hero.jpg",
                f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
                f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/capsule_616x353.jpg"
            ]
        else:
            cover_urls_to_try = [
                f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
            ]

        for cover_url in cover_urls_to_try:
            try:
                response = requests.get(cover_url, stream=True, timeout=10)
                response.raise_for_status()

                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                load_success = pixmap.loadFromData(image_data.getvalue())

                if not pixmap.isNull() and load_success:
                    scaled_pixmap = pixmap.scaled(target_label.size(),
                                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                   Qt.TransformationMode.SmoothTransformation)
                    target_label.setPixmap(scaled_pixmap)
                    return

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    pass
                else:
                    print(f"ERROR: HTTP Error for {cover_url}: {e.response.status_code} - {e.response.reason}. Trying next option.")
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request error for {cover_url}: {e}. Trying next option.")
            except Exception as e:
                print(f"ERROR: Unexpected error loading {cover_url}: {e}. Trying next option.")

        target_label.clear()
        target_label.setText(f"No cover for {appid}")
        target_label.setStyleSheet("border: 1px solid red; border-radius: 5px; color: red;")
        print(f"Failed to load any cover for AppID {appid}.")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and isinstance(obj, QLabel):
            game_info = obj.property("game_info")
            if game_info:
                self.show_game_details(game_info)
                return True
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Type.Wheel:
            h_bar = self.scroll_area.horizontalScrollBar()

            scroll_amount = 50

            if event.angleDelta().y() > 0:
                h_bar.setValue(h_bar.value() - scroll_amount)
            else:
                h_bar.setValue(h_bar.value() + scroll_amount)

            return True

        return super().eventFilter(obj, event)

    def show_game_details(self, game_info):
        self.selected_game_info = game_info
        print(f"Showing details for: {game_info.get('name')}")

        self.detail_game_name_label.setText(game_info.get('name', 'N/A'))
        self.display_cover_on_label(game_info.get('appid'), self.detail_cover_label, cover_type='detail')
        self.detail_info_label.setText(f"AppID: {game_info.get('appid', 'N/A')}\n"
                                       f"Install Path: {game_info.get('full_install_path', 'N/A')}\n"
                                       f"Some future ML data or description goes here...")
        self.detail_launch_button.setEnabled(True)
        
        self.stacked_widget.setCurrentWidget(self.game_details_page)
        self.back_button.show()

    def launch_game_from_details(self):
        if self.selected_game_info and self.selected_game_info.get('appid'):
            appid = self.selected_game_info['appid']
            print(f"Launching game (AppID: {appid})...")
            QDesktopServices.openUrl(QUrl(f"steam://rungameid/{appid}"))
        else:
            print("No game selected for launch from details page.")

    def go_back_to_game_list(self):
        self.stacked_widget.setCurrentWidget(self.game_list_page)
        self.back_button.hide()
        self.detail_cover_label.clear()
        self.detail_game_name_label.setText("Game Name")
        self.detail_info_label.setText("Additional info here (ML, stats, description...)")
        self.detail_launch_button.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameLauncherApp()
    window.show()
    sys.exit(app.exec())