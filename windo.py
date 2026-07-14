"""
MathPad - 手写数学公式识别工具
Step 1: 基础窗口
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MathPadWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathPad")
        self.setFixedSize(800, 400)
        self._init_ui()

    def _init_ui(self):
        # 中心组件
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ---- 书写区域 ----
        self.canvas = QFrame()
        self.canvas.setMinimumHeight(280)
        self.canvas.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #888;
                border-radius: 4px;
            }
        """)
        self.canvas.setCursor(Qt.CursorShape.CrossCursor)

        main_layout.addWidget(self.canvas, stretch=1)

        # ---- 底部控制栏 ----
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        # 输出框
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
