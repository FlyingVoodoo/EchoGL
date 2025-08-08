# python_modules/ui/animated_widgets.py
from PyQt6.QtWidgets import (
    QStackedWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QLabel
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSize,
    pyqtProperty, QTimer, QEvent 
)
from PyQt6.QtGui import QPixmap, QColor, QPainter

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fade_duration = 350
        self._is_animating = False

        self._out_animation = QPropertyAnimation()
        self._out_animation.setPropertyName(b"opacity")
        self._out_animation.setDuration(self._fade_duration)
        self._out_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self._in_animation = QPropertyAnimation()
        self._in_animation.setPropertyName(b"opacity")
        self._in_animation.setDuration(self._fade_duration)
        self._in_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self._in_animation.finished.connect(self._on_in_animation_finished)

        self._target_index = -1
        self._current_out_widget = None
        self._current_in_widget = None
        self._active_out_effect = None
        self._active_in_effect = None

    def setAnimationDuration(self, ms):
        self._fade_duration = ms
        self._out_animation.setDuration(ms)
        self._in_animation.setDuration(ms)

    def setCurrentIndex(self, index):
        if index == self.currentIndex() or self._is_animating:
            return

        old_widget = self.currentWidget()
        new_widget = self.widget(index)
        
        if not old_widget or not new_widget:
            super().setCurrentIndex(index)
            return

        self._is_animating = True
        self._target_index = index

        self._current_out_widget = old_widget
        self._current_in_widget = new_widget

        if old_widget.graphicsEffect():
            old_widget.setGraphicsEffect(None)

        self._active_out_effect = QGraphicsOpacityEffect(old_widget)
        old_widget.setGraphicsEffect(self._active_out_effect)
        self._active_out_effect.setOpacity(1.0)

        if new_widget.graphicsEffect():
            new_widget.setGraphicsEffect(None)

        self._active_in_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(self._active_in_effect)
        new_widget.show()
        self._active_in_effect.setOpacity(0.0)

        self._out_animation.setTargetObject(self._active_out_effect)
        self._out_animation.setStartValue(1.0)
        self._out_animation.setEndValue(0.0)
        
        self._in_animation.setTargetObject(self._active_in_effect)
        self._in_animation.setStartValue(0.0)
        self._in_animation.setEndValue(1.0)
        
        try:
            self._out_animation.finished.disconnect(self._on_out_animation_finished_and_switch)
        except TypeError:
            pass
        self._out_animation.finished.connect(self._on_out_animation_finished_and_switch)
        
        self._out_animation.start()

    def _on_out_animation_finished_and_switch(self):
        try:
            self._out_animation.finished.disconnect(self._on_out_animation_finished_and_switch)
        except TypeError:
            pass

        if self._current_out_widget and self._active_out_effect:
            if self._current_out_widget.graphicsEffect() is self._active_out_effect:
                self._current_out_widget.setGraphicsEffect(None)
            self._active_out_effect = None 
        self._current_out_widget = None

        super().setCurrentIndex(self._target_index)
        self._in_animation.start()

    def _on_in_animation_finished(self):
        if self._current_in_widget and self._active_in_effect:
            if self._current_in_widget.graphicsEffect() is self._active_in_effect:
                self._current_in_widget.setGraphicsEffect(None)
            self._active_in_effect = None
        self._current_in_widget = None
        self._is_animating = False
        self._target_index = -1

    def setCurrentWidget(self, widget):
        index = self.indexOf(widget)
        self.setCurrentIndex(index)


class AnimatedCoverLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_size = QSize(180, 270)
        self.setFixedSize(self.original_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContentsMargins(0, 0, 0, 0)

        self._original_pixmap = QPixmap()

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(0)
        self.shadow_effect.setColor(QColor(255, 255, 255, 150))
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)

        self._size_animation = QPropertyAnimation(self, b"")
        self._size_animation.setDuration(150)
        self._size_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self.glow_animation = QPropertyAnimation(self.shadow_effect, b"blurRadius")
        self.glow_animation.setDuration(150)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.installEventFilter(self)
    
    @pyqtProperty(QSize)
    def animatedSize(self):
        return self.size()

    @animatedSize.setter
    def animatedSize(self, size: QSize):
        self.setFixedSize(size)
        if not self._original_pixmap.isNull():
            self._update_displayed_pixmap()

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Type.Enter:
                self.animate_tile_scale(1.2)
                self.animate_glow(20)
            elif event.type() == QEvent.Type.Leave:
                self.animate_tile_scale(1.0)
                self.animate_glow(0)
        return super().eventFilter(obj, event)

    def animate_tile_scale(self, factor):
        if self._size_animation.state() == QPropertyAnimation.State.Running:
            self._size_animation.stop()

        new_width = int(self.original_size.width() * factor)
        new_height = int(self.original_size.height() * factor)
        
        self._size_animation.setTargetObject(self)
        self._size_animation.setPropertyName(b"animatedSize")
        self._size_animation.setStartValue(self.size())
        self._size_animation.setEndValue(QSize(new_width, new_height))
        self._size_animation.start()

    def animate_glow(self, blur_radius):
        if self.glow_animation.state() == QPropertyAnimation.State.Running:
            self.glow_animation.stop()

        self.glow_animation.setStartValue(self.shadow_effect.blurRadius())
        self.glow_animation.setEndValue(blur_radius)
        self.glow_animation.start()

    def setOriginalPixmap(self, pixmap: QPixmap):
        self._original_pixmap = pixmap
        self._update_displayed_pixmap()

    def _update_displayed_pixmap(self):
        if self._original_pixmap.isNull():
            super().setPixmap(QPixmap())
            return
            # Создаем новый QPixmap для буфера, такого же размера как виджет
    # и заполняем его прозрачным цветом
        new_pixmap = QPixmap(self.size())
        new_pixmap.fill(Qt.GlobalColor.transparent)

        # Создаем QPainter для рисования на буфере
        painter = QPainter(new_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Масштабируем оригинальное изображение под текущий размер метки
        scaled_pixmap = self._original_pixmap.scaled(self.size(),
                                                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                    Qt.TransformationMode.SmoothTransformation)

        # Рассчитываем позицию для центрирования изображения
        x = (self.width() - scaled_pixmap.width()) / 2
        y = (self.height() - scaled_pixmap.height()) / 2

        # Рисуем масштабированное изображение на буфере
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        painter.end() # Важно явно закрыть painter после использования!

        # Устанавливаем буферизированное изображение в метку
        super().setPixmap(new_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def showEvent(self, event): 
        if self.shadow_effect:
            self.shadow_effect.setEnabled(True)
        super().showEvent(event)

    def hideEvent(self, event): 
        if self.shadow_effect:
            self.shadow_effect.setEnabled(False)
        super().hideEvent(event)