# python_modules/ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
)
from PyQt6.QtCore import Qt, QUrl, QTimer 
from PyQt6.QtGui import QDesktopServices

from pathlib import Path

from ui.animated_widgets import AnimatedStackedWidget
from ui.game_list_page import GameListPage
from ui.game_details_page import GameDetailsPage
from core.game_manager import GameManager 

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("EchoGL")
        self.setGeometry(100, 100, 1200, 800)

        style_file = Path(__file__).parent.parent / "assets" / "style.qss"

        if style_file.exists():
            with open(style_file, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Error: style.qss not found at {style_file}. Styles will not be applied.")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.game_manager = GameManager(self)
        self.game_manager.scan_started.connect(self._on_scan_started)
        self.game_manager.scan_finished.connect(self._on_scan_finished)
        self.game_manager.game_launched.connect(self._on_game_launched)

        self.game_manager.request_display_cover.connect(self.game_manager.display_cover_on_label)


        self.title_label = QLabel("Echo Game Launcher")
        self.title_label.setObjectName("launcherTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        self.scan_button = QPushButton("Scan Steam Games")
        self.scan_button.clicked.connect(self.game_manager.scan_for_games)
        self.main_layout.addWidget(self.scan_button)

        self.stacked_widget = AnimatedStackedWidget()
        self.stacked_widget.setAnimationDuration(350)
        self.main_layout.addWidget(self.stacked_widget)

        self.game_list_page = GameListPage(self.game_manager)
        self.stacked_widget.addWidget(self.game_list_page)
        self.game_list_page.game_selected.connect(self._show_game_details)

        self.game_details_page = GameDetailsPage(self.game_manager)
        self.stacked_widget.addWidget(self.game_details_page)
        self.game_details_page.launch_game_requested.connect(self.game_manager.launch_game)

        self.stacked_widget.setCurrentWidget(self.game_list_page)

        self.back_button = QPushButton("Back to Games List")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self._go_back_to_game_list)
        self.back_button.hide()
        self.main_layout.addWidget(self.back_button)

    def _on_scan_started(self):
        self.scan_button.setEnabled(False)
        self.title_label.setText("Scanning games... Please wait.")

    def _on_scan_finished(self, games_list: list):
        self.scan_button.setEnabled(True)
        self.title_label.setText("Echo Game Launcher")
        self.game_list_page.display_games(games_list)
        
        if self.stacked_widget.currentWidget() != self.game_list_page:
            self.stacked_widget.setCurrentWidget(self.game_list_page)
            self.back_button.hide()


    def _on_game_launched(self, appid: str):
        print(f"UI подтверждает: Игра {appid} была запущена.")

    def _show_game_details(self, game_info: dict):
        self.game_details_page.set_game_info(game_info)
        self.stacked_widget.setCurrentWidget(self.game_details_page)
        self.back_button.show()

    def _go_back_to_game_list(self):
        self.stacked_widget.setCurrentWidget(self.game_list_page)
        self.back_button.hide()
        # self.game_details_page.clear_info()

        self.game_list_page.scroll_content_widget.adjustSize()
        self.game_list_page.scroll_layout.update()
        self.game_list_page.scroll_area.viewport().update()

        QTimer.singleShot(0, self._fix_layout)

    def _fix_layout(self):
        self.game_list_page.scroll_content_widget.updateGeometry()
        self.game_list_page.scroll_layout.update()
        self.game_list_page.scroll_area.updateGeometry()

    def closeEvent(self, event):
        self.game_manager.close_db()
        super().closeEvent(event)
        event.accept()