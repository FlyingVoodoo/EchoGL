from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QEvent, pyqtSignal, QObject # Добавил QObject для сигналов

from ui.animated_widgets import AnimatedCoverLabel

class GameListPage(QWidget):
    game_selected = pyqtSignal(dict)

    def __init__(self, game_manager, parent=None):
        super().__init__(parent)
        self.game_manager = game_manager 

        self.page_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(20)

        self.scroll_area.setWidget(self.scroll_content_widget)
        self.page_layout.addWidget(self.scroll_area)

        self.scroll_area.viewport().installEventFilter(self)

    def display_games(self, games_list: list):
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and hasattr(item.widget(), 'setEnabled'):
                item.widget().setEnabled(False)

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not games_list:
            no_games_label = QLabel("No Steam games found.")
            no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_games_label)
            return

        for game in games_list:
            cover_label = AnimatedCoverLabel()
            cover_label.setProperty("game_info", game) 

            cover_label.mousePressEvent = lambda event, info=game: self.game_selected.emit(info)

            self.scroll_layout.addWidget(cover_label)
            self.game_manager.request_display_cover.emit(
                str(game.get('appid')), cover_label, 'thumbnail', True
            )

        self.scroll_layout.addStretch()

        self.scroll_content_widget.adjustSize()
        self.scroll_layout.update()
        self.scroll_area.viewport().update()

    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Type.Wheel:
            h_bar = self.scroll_area.horizontalScrollBar()
            scroll_amount = 50
            if event.angleDelta().y() > 0:
                h_bar.setValue(h_bar.value() - scroll_amount)
            else:
                h_bar.setValue(h_bar.value() + scroll_amount)
            return True
        return super().eventFilter(obj, event)