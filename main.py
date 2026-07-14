"""
MathPad - 手写数学公式识别工具
"""
import sys
import subprocess
import os
import re
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSlider, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QImage


# ═══════════════════════════════════════════
# LaTeX → Unicode 转换
# ═══════════════════════════════════════════

_SYMBOLS = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\varepsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η',
    r'\theta': 'θ', r'\vartheta': 'ϑ', r'\iota': 'ι', r'\kappa': 'κ',
    r'\lambda': 'λ', r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ',
    r'\pi': 'π', r'\varpi': 'ϖ', r'\rho': 'ρ', r'\sigma': 'σ',
    r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ', r'\varphi': 'φ',
    r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Omega': 'Ω',
    r'\times': '×', r'\div': '÷', r'\pm': '±', r'\cdot': '·',
    r'\circ': '○', r'\bullet': '•', r'\star': '★', r'\ast': '∗',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\approx': '≈',
    r'\equiv': '≡', r'\sim': '∼', r'\propto': '∝',
    r'\rightarrow': '→', r'\to': '→', r'\leftarrow': '←', r'\gets': '←',
    r'\Rightarrow': '⇒', r'\Leftarrow': '⇐', r'\leftrightarrow': '↔',
    r'\Leftrightarrow': '⇔', r'\mapsto': '↦',
    r'\sum': '∑', r'\prod': '∏', r'\int': '∫', r'\iint': '∬',
    r'\oint': '∮', r'\bigcup': '⋃', r'\bigcap': '⋂',
    r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇',
    r'\forall': '∀', r'\exists': '∃', r'\emptyset': '∅',
    r'\sqrt': '√', r'\angle': '∠', r'\parallel': '∥', r'\perp': '⊥',
    r'\in': '∈', r'\notin': '∉', r'\subset': '⊂', r'\supset': '⊃',
    r'\subseteq': '⊆', r'\wedge': '∧', r'\vee': '∨', r'\neg': '¬',
    r'\ldots': '…', r'\cdots': '⋯', r'\vdots': '⋮', r'\ddots': '⋱',
    r'\prime': '′', r'\hbar': 'ℏ', r'\ell': 'ℓ',
}

_sorted_keys = sorted(_SYMBOLS.keys(), key=len, reverse=True)
_SYMBOL_RE = re.compile('|'.join(re.escape(k) for k in _sorted_keys))

_SUPER = str.maketrans('0123456789+-=()', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾')
_SUB   = str.maketrans('0123456789+-=()', '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎')


def latex_to_unicode(latex: str) -> str:
    """LaTeX → 可复制的 Unicode 数学文本"""
    s = latex.strip()

    # 去掉格式命令
    for cmd in (r'\mathbf', r'\boldsymbol', r'\mathit', r'\mathrm',
                r'\mathcal', r'\text', r'\scriptstyle', r'\displaystyle',
                r'\limits', r'\scriptstyle'):
        s = re.sub(re.escape(cmd) + r'\{([^}]*)\}', r'\1', s)

    # 上标 ^{...}
    def _super(m):
        inner = m.group(1)
        return inner.translate(_SUPER) if len(inner) == 1 else _to_super(inner)
    s = re.sub(r'\^\{([^}]*)\}', _super, s)
    s = re.sub(r'\^(\S)', lambda m: m.group(1).translate(_SUPER), s)

    # 下标 _{...}
    def _sub(m):
        inner = m.group(1)
        return inner.translate(_SUB) if len(inner) == 1 else '_' + inner
    s = re.sub(r'_\{([^}]*)\}', _sub, s)
    s = re.sub(r'_(\S)', lambda m: m.group(1).translate(_SUB), s)

    # 去花括号
    s = re.sub(r'\{([^{}]*)\}', r'\1', s)
    # 替换符号
    s = _SYMBOL_RE.sub(lambda m: _SYMBOLS[m.group()], s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _to_super(s: str) -> str:
    return re.sub(r'[a-zA-Z0-9+\-=()]',
                  lambda m: m.group().translate(_SUPER), s)


# ═══════════════════════════════════════════
# Canvas
# ═══════════════════════════════════════════

class Canvas(QFrame):
    """手写画布"""

    PEN_COLOR = QColor(180, 180, 180)   # 浅灰笔迹
    BG_COLOR  = "#1e1e1e"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strokes = []
        self.current_stroke = []
        self.setMinimumHeight(280)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self.BG_COLOR))
        pen = QPen(self.PEN_COLOR, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for stroke in self.strokes:
            self._draw_stroke(painter, stroke)
        if self.current_stroke:
            self._draw_stroke(painter, self.current_stroke)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_stroke = [event.pos()]

    def mouseMoveEvent(self, event):
        if self.current_stroke:
            self.current_stroke.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_stroke:
            self.current_stroke.append(event.pos())
            self.strokes.append(self.current_stroke)
            self.current_stroke = []
            self.update()

    def _draw_stroke(self, painter, stroke):
        if len(stroke) < 2:
            painter.drawPoint(stroke[0])
            return
        for i in range(len(stroke) - 1):
            painter.drawLine(stroke[i], stroke[i + 1])

    def clear(self):
        self.strokes = []
        self.current_stroke = []
        self.update()

    def to_image(self, filepath="temp.png"):
        """黑底白字 → 白底黑字（给模型用）"""
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


# ═══════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════

class MathPadWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathPad")
        self.setFixedSize(800, 420)
        self._proc = None
        self._model_ready = False
        self._last_latex = ""
        self._display_mode = 0  # 0=Text  1=LaTeX
        self._init_ui()
        self._start_worker()

    # ── 进程管理 ──

    def _start_worker(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(base_dir, "unimernet_infer.py")
        self._proc = subprocess.Popen(
            [r"D:\anaconda\envs\unimernet\python.exe", script],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
        )

        def wait_ready():
            line = self._proc.stdout.readline()
            if line.strip() == "READY":
                self._model_ready = True

        threading.Thread(target=wait_ready, daemon=True).start()

    def _on_model_ready(self):
        if self._model_ready:
            self._ready_timer.stop()
            self.result_line.setPlaceholderText("Write & click Recognize...")

    def closeEvent(self, event):
        if self._proc is not None:
            try:
                self._proc.stdin.write("__EXIT__\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
        super().closeEvent(event)

    # ── 显示 ──

    def _show_result(self):
        if self._display_mode == 0:
            self.result_line.setText(latex_to_unicode(self._last_latex))
        else:
            self.result_line.setText(self._last_latex)

    # ── UI ──

    STYLE = """
        QMainWindow, QWidget {
            background: #1e1e1e;
            color: #cccccc;
            font-family: "Segoe UI", "Cascadia Code", sans-serif;
            font-size: 13px;
        }
        QLineEdit {
            background: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
            border-radius: 3px;
            padding: 4px 8px;
            selection-background-color: #264f78;
        }
        QLineEdit:focus {
            border-color: #0078d4;
        }
        QPushButton {
            background: #0e639c;
            color: #ffffff;
            border: none;
            border-radius: 3px;
            padding: 5px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: #1177bb;
        }
        QPushButton:pressed {
            background: #094771;
        }
        QPushButton:disabled {
            background: #3c3c3c;
            color: #707070;
        }
        QLabel {
            color: #cccccc;
            background: transparent;
        }
        QSlider::groove:horizontal {
            background: #4a4a4a;
            height: 4px;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #0078d4;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }
        QSlider::handle:horizontal:hover {
            background: #1a8ad4;
        }
    """

    def _init_ui(self):
        self.setStyleSheet(self.STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 8)
        main_layout.setSpacing(5)

        self.canvas = Canvas()
        self.canvas.setStyleSheet("QFrame { border: 1px solid #3c3c3c; border-radius: 4px; }")
        main_layout.addWidget(self.canvas, stretch=1)

        font = QFont("Segoe UI", 12)

        # 结果行
        result_row = QHBoxLayout()
        result_row.setSpacing(8)
        lbl = QLabel("Result")
        lbl.setFont(font)
        lbl.setStyleSheet("color: #858585;")
        result_row.addWidget(lbl)

        self.result_line = QLineEdit()
        self.result_line.setReadOnly(True)
        self.result_line.setPlaceholderText("Model loading...")
        self.result_line.setFont(font)
        self.result_line.setMinimumHeight(32)
        result_row.addWidget(self.result_line, stretch=1)
        main_layout.addLayout(result_row)

        # 控制行
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        self.mode_label_left = QLabel("Text")
        ctrl_row.addWidget(self.mode_label_left)

        self.mode_slider = QSlider(Qt.Orientation.Horizontal)
        self.mode_slider.setRange(0, 1)
        self.mode_slider.setValue(0)
        self.mode_slider.setFixedWidth(36)
        self.mode_slider.valueChanged.connect(self._on_mode_changed)
        ctrl_row.addWidget(self.mode_slider)

        self.mode_label_right = QLabel("LaTeX")
        ctrl_row.addWidget(self.mode_label_right)

        ctrl_row.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear)
        ctrl_row.addWidget(self.clear_btn)

        self.recognize_btn = QPushButton("Recognize")
        self.recognize_btn.clicked.connect(self._on_recognize)
        ctrl_row.addWidget(self.recognize_btn)

        main_layout.addLayout(ctrl_row)

        self._ready_timer = QTimer()
        self._ready_timer.timeout.connect(self._on_model_ready)
        self._ready_timer.start(200)

        # 初始高亮 Text 模式
        self.mode_label_left.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.mode_label_right.setStyleSheet("color: #858585;")

    # ── 回调 ──

    def _on_mode_changed(self, value):
        self._display_mode = value
        if value == 0:
            self.mode_label_left.setStyleSheet("color: #ffffff; font-weight: bold;")
            self.mode_label_right.setStyleSheet("color: #858585;")
        else:
            self.mode_label_left.setStyleSheet("color: #858585;")
            self.mode_label_right.setStyleSheet("color: #ffffff; font-weight: bold;")
        if self._last_latex:
            self._show_result()

    def _on_clear(self):
        if not self._model_ready:
            return
        self.canvas.clear()
        self._last_latex = ""
        self.result_line.clear()

    def _on_recognize(self):
        if not self._model_ready:
            self.result_line.setText("Model Initializing...")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = self.canvas.to_image(os.path.join(base_dir, "temp.png"))

        self.result_line.setText("识别中...")
        QApplication.processEvents()

        try:
            self._proc.stdin.write(filepath + "\n")
            self._proc.stdin.flush()
            raw = self._proc.stdout.readline().strip()
            if raw.startswith("ERROR:"):
                self.result_line.setText(f"识别失败: {raw[6:]}")
            else:
                self._last_latex = raw
                self._show_result()
        except Exception as e:
            self.result_line.setText(f"通信失败: {e}")
            self._proc = None
            self._model_ready = False


def main():
    app = QApplication(sys.argv)
    window = MathPadWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
