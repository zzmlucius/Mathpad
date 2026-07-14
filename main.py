"""
MathPad - 手写数学公式识别工具
Step 1-5: 窗口 + 手写 + 按钮 + 图片生成 + 识别
"""

import sys
import subprocess
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QImage


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

    # ---- 笔迹转图片 (Step 4) ----
    def to_image(self, filepath="temp.png"):
        """将笔迹渲染为 PNG 图片"""
        image = QImage(self.size(), QImage.Format.Format_RGB32)
        image.fill(QColor(255, 255, 255))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(0, 0, 0), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        for stroke in self.strokes:
            self._draw_stroke(painter, stroke)

        painter.end()
        image.save(filepath)
        return filepath


class MathPadWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathPad")
        self.setFixedSize(800, 400)
        self._proc = None  # 常驻识别进程
        self._init_ui()

    def _ensure_worker(self):
        """启动常驻识别进程（仅首次调用时加载模型）"""
        if self._proc is not None:
            return True

        base_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(base_dir, "unimernet_infer.py")

        self._proc = subprocess.Popen(
            [r"D:\anaconda\envs\unimernet\python.exe", script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        # 等待模型加载完成（READY信号）
        ready = self._proc.stdout.readline()
        if ready.strip() != "READY":
            self.result_line.setText("模型启动失败")
            self._proc = None
            return False
        return True

    def closeEvent(self, event):
        """关闭窗口时终止识别进程"""
        if self._proc is not None:
            try:
                self._proc.stdin.write("__EXIT__\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
        super().closeEvent(event)

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

        # ---- 按钮 (Step 3) ----
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.canvas.clear)
        bottom.addWidget(clear_btn)

        recognize_btn = QPushButton("Recognize")
        recognize_btn.clicked.connect(self._on_recognize)
        bottom.addWidget(recognize_btn)

        main_layout.addLayout(bottom)

    def _on_recognize(self):
        """Step 4: 笔迹 → 图片  →  Step 5: UniMERNet 识别（常驻进程）"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = self.canvas.to_image(os.path.join(base_dir, "temp.png"))

        # 首次调用需加载模型，后续复用常驻进程
        is_first = self._proc is None
        self.result_line.setText("正在加载模型..." if is_first else "识别中...")
        QApplication.processEvents()

        if not self._ensure_worker():
            return

        try:
            self._proc.stdin.write(filepath + "\n")
            self._proc.stdin.flush()
            result = self._proc.stdout.readline().strip()
            if result.startswith("ERROR:"):
                self.result_line.setText(f"识别失败: {result[6:]}")
            else:
                self.result_line.setText(result)
        except Exception as e:
            self.result_line.setText(f"通信失败: {e}")
            self._proc = None


def main():
    app = QApplication(sys.argv)
    window = MathPadWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
