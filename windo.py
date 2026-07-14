"""
MathPad - 手写数学公式识别工具
Step 2: 手写功能
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QPainter, QPen, QColor


class Canvas(QFrame):
    """手写画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strokes = []          # 所有完成的笔画
        self.current_stroke = []   # 当前正在画的笔画
        self.setMinimumHeight(280)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #888;
                border-radius: 4px;
            }
        """)
        self.setCursor(Qt.CursorShape.CrossCursor)
        # 开启鼠标追踪，确保 mouseMoveEvent 在不按鼠标时也能触发（本项目中不需，
        # 但设为 True 可保证按住鼠标移动时事件流畅）
        self.setMouseTracking(True)

    # ---- 鼠标事件 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_stroke = [event.pos()]
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_stroke:
            self.current_stroke.append(event.pos())
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_stroke:
            self.current_stroke.append(event.pos())
            self.strokes.append(self.current_stroke)
            self.current_stroke = []
            self.update()
        super().mouseReleaseEvent(event)

    # ---- 绘制 ----
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(0, 0, 0), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # 绘制已完成的笔画
        for stroke in self.strokes:
            self._draw_stroke(painter, stroke)

        # 绘制当前正在画的笔画
        if self.current_stroke:
            self._draw_stroke(painter, self.current_stroke)

        painter.end()

    def _draw_stroke(self, painter, stroke):
        if len(stroke) < 2:
            # 单点：画一个小圆点
            p = stroke[0]
            painter.drawPoint(p)
            return
        for i in range(len(stroke) - 1):
            painter.drawLine(stroke[i], stroke[i + 1])

    # ---- 清空 ----
    def clear(self):
        self.strokes = []
        self.current_stroke = []
        self.update()


class MathPadWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathPad")
        self.setFixedSize(800, 400)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ---- 书写区域 ----
        self.canvas = Canvas()

        main_layout.addWidget(self.canvas, stretch=1)

        # ---- 底部控制栏 ----
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        result_label = QLabel("Result:")
        font = QFont()
        font.setPointSize(12)
        result_label.setFont(font)
        bottom.addWidget(result_label)

        self.result_line = QLineEdit()
        self.result_line.setReadOnly(True)
        self.result_line.setPlaceholderText("识别结果将显示在这里...")
        self.result_line.setFont(font)
        self.result_line.setMinimumHeight(30)
        bottom.addWidget(self.result_line, stretch=1)

        main_layout.addLayout(bottom)


def main():
    app = QApplication(sys.argv)
    window = MathPadWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
