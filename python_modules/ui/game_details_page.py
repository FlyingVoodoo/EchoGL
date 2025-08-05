from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QObject

class GameDetailsPage(QWidget):
    launch_game_requested = pyqtSignal(str) 

    def __init__(self, game_manager, parent=None):
        super().__init__(parent)
        self.game_manager = game_manager

        self.page_layout = QVBoxLayout(self) 

        self.detail_content_widget = QWidget()
        self.detail_content_widget.setObjectName("detailPanel")
        self.detail_content_layout = QVBoxLayout(self.detail_content_widget)

        self.detail_cover_label = QLabel()
        self.detail_cover_label.setObjectName("detailCoverLabel")
        self.detail_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_cover_label.setFixedSize(800, 300) 
        
        self.detail_game_name_label = QLabel("Game Name")
        self.detail_game_name_label.setObjectName("detailTitle")
        self.detail_game_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.detail_launch_button = QPushButton("Launch Game")
        self.detail_launch_button.clicked.connect(lambda: self.launch_game_requested.emit(self._current_appid))
        
        self.detail_info_label = QLabel("Additional info here (ML, stats, description...)")
        self.detail_info_label.setObjectName("detailText")
        self.detail_info_label.setWordWrap(True)

        self.detail_content_layout.addWidget(self.detail_cover_label)
        self.detail_content_layout.addWidget(self.detail_game_name_label)
        self.detail_content_layout.addWidget(self.detail_launch_button)
        self.detail_content_layout.addWidget(self.detail_info_label)
        self.detail_content_layout.addStretch()
        
        self.page_layout.addWidget(self.detail_content_widget)
        self.page_layout.addStretch()

        self._current_appid = None 

    def set_game_info(self, game_info: dict):
        self._current_appid = game_info.get('appid')
        
        self.detail_game_name_label.setText(game_info.get('name', 'N/A'))
        self.detail_info_label.setText(f"AppID: {game_info.get('appid', 'N/A')}\n"
                                         f"Install Path: {game_info.get('install_path', 'N/A')}\n"
                                         f"Some future ML data or description goes here...")
        
        self.detail_launch_button.setEnabled(bool(self._current_appid)) 
        
        self.game_manager.request_display_cover.emit(
            str(game_info.get('appid')), self.detail_cover_label, 'detail', True
        )

    def clear_info(self):
        self._current_appid = None
        self.detail_cover_label.clear()
        self.detail_game_name_label.setText("Game Name")
        self.detail_info_label.setText("Additional info here (ML, stats, description...)")
        self.detail_launch_button.setEnabled(False)