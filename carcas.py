import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QScrollArea,
    QToolBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont


# ─── Стили ──────────────────────────────────────────────────────────────────

STYLE = """
QMainWindow {
    background-color: #f0f0f0;
}
QWidget#central {
    background-color: #f0f0f0;
}

/* Секции */
QFrame#section {
    background-color: #f8f8f8;
    border: 1px solid #cccccc;
    border-radius: 4px;
}
QLabel#sectionTitle {
    color: #555555;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 1px;
    background: transparent;
}

/* Output display */
QTextEdit#outputDisplay {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    color: #aaaaaa;
    font-size: 12px;
    letter-spacing: 2px;
}

/* Ячейки ротора */
QPushButton#rotorCell {
    background-color: #ffffff;
    border: 1px solid #333333;
    font-size: 13px;
    font-weight: bold;
    min-width: 36px;
    min-height: 30px;
    max-width: 36px;
    max-height: 30px;
}
QPushButton#rotorCellActive {
    background-color: #ffffff;
    border: 2px solid #333333;
    font-size: 14px;
    font-weight: bold;
    min-width: 36px;
    min-height: 34px;
    max-width: 36px;
    max-height: 34px;
}
QPushButton#rotorArrow {
    background-color: #ffffff;
    border: 1px solid #333333;
    font-size: 10px;
    min-width: 28px;
    min-height: 24px;
    max-width: 28px;
    max-height: 24px;
}

/* Лампы */
QPushButton#lamp {
    background-color: #e0e0e0;
    border: 1px solid #999999;
    border-radius: 14px;
    min-width: 28px;
    min-height: 28px;
    max-width: 28px;
    max-height: 28px;
    font-size: 8px;
    color: #555555;
}
QPushButton#lampOn {
    background-color: #ffffaa;
    border: 2px solid #ccaa00;
    border-radius: 14px;
    min-width: 28px;
    min-height: 28px;
    max-width: 28px;
    max-height: 28px;
    font-size: 8px;
    color: #333300;
    font-weight: bold;
}

/* Клавиши клавиатуры */
QPushButton#key {
    background-color: #ffffff;
    border: 1px solid #333333;
    border-radius: 3px;
    font-size: 12px;
    font-weight: bold;
    min-width: 40px;
    min-height: 38px;
    max-width: 40px;
    max-height: 38px;
}
QPushButton#key:pressed {
    background-color: #dddddd;
}

/* Plugboard */
QPushButton#addConnection {
    background-color: #ffffff;
    border: 1px solid #333333;
    font-size: 11px;
    padding: 8px 20px;
    min-width: 160px;
}
QPushButton#addConnection:hover {
    background-color: #f0f0f0;
}
QTextEdit#plugboardDisplay {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    font-size: 11px;
}

/* Кнопки внизу */
QPushButton#bottomBtn {
    background-color: #ffffff;
    border: 1px solid #333333;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
    min-width: 120px;
    min-height: 36px;
}
QPushButton#bottomBtn:hover {
    background-color: #f0f0f0;
}

/* Тулбар */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #cccccc;
    spacing: 4px;
}
QPushButton#toolBtn {
    background-color: transparent;
    border: 1px solid #cccccc;
    border-radius: 3px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
    font-size: 13px;
}
QPushButton#toolBtn:hover {
    background-color: #f0f0f0;
}
"""

KEYBOARD_ROWS = [
    list("QWERTZUIO"),
    list("ASDFGHJK"),
    list("PYXCVBNML"),
]


# ─── Виджет ротора ───────────────────────────────────────────────────────────

class RotorWidget(QWidget):
    """Один ротор: три ячейки с буквами + кнопки ▲/▼."""

    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, name: str, initial: str = "B", parent=None):
        super().__init__(parent)
        self._pos = self.ALPHABET.index(initial)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel(name)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 8))
        title.setStyleSheet("color:#555; font-size:9px; letter-spacing:1px;")
        layout.addWidget(title)

        # Три ячейки: пред., текущая (выделена), след.
        self._btn_prev = QPushButton(self._letter(-1))
        self._btn_prev.setObjectName("rotorCell")
        self._btn_curr = QPushButton(self._letter(0))
        self._btn_curr.setObjectName("rotorCellActive")
        self._btn_next = QPushButton(self._letter(1))
        self._btn_next.setObjectName("rotorCell")

        for btn in (self._btn_prev, self._btn_curr, self._btn_next):
            btn.setEnabled(False)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Кнопки управления
        arrow_layout = QHBoxLayout()
        arrow_layout.setSpacing(2)
        self._btn_up = QPushButton("▲")
        self._btn_up.setObjectName("rotorArrow")
        self._btn_dn = QPushButton("▼")
        self._btn_dn.setObjectName("rotorArrow")
        arrow_layout.addWidget(self._btn_up)
        arrow_layout.addWidget(self._btn_dn)
        layout.addLayout(arrow_layout)

        self._btn_up.clicked.connect(self._step_up)
        self._btn_dn.clicked.connect(self._step_down)

    def _letter(self, offset: int) -> str:
        return self.ALPHABET[(self._pos + offset) % 26]

    def _refresh(self):
        self._btn_prev.setText(self._letter(-1))
        self._btn_curr.setText(self._letter(0))
        self._btn_next.setText(self._letter(1))

    def _step_up(self):
        self._pos = (self._pos - 1) % 26
        self._refresh()

    def _step_down(self):
        self._pos = (self._pos + 1) % 26
        self._refresh()

    def get_position(self) -> str:
        return self.ALPHABET[self._pos]


# ─── Лампборд ────────────────────────────────────────────────────────────────

class LampboardWidget(QWidget):
    """Сетка ламп (по раскладке клавиатуры Enigma)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lamps: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        for row in KEYBOARD_ROWS:
            row_widget = QHBoxLayout()
            row_widget.setSpacing(4)
            row_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            for letter in row:
                btn = QPushButton(letter)
                btn.setObjectName("lamp")
                btn.setEnabled(False)
                self._lamps[letter] = btn
                row_widget.addWidget(btn)
            layout.addLayout(row_widget)

    def light_up(self, letter: str):
        """Включить лампу."""
        if letter in self._lamps:
            self._lamps[letter].setObjectName("lampOn")
            self._lamps[letter].setStyle(self._lamps[letter].style())

    def reset_lights(self):
        """Погасить все лампы."""
        for letter, btn in self._lamps.items():
            btn.setObjectName("lamp")
            btn.setStyle(btn.style())


# ─── Клавиатура ──────────────────────────────────────────────────────────────

class KeyboardWidget(QWidget):
    """Физическая клавиатура Enigma."""

    def __init__(self, on_key_pressed, parent=None):
        super().__init__(parent)
        self._callback = on_key_pressed

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        for row in KEYBOARD_ROWS:
            row_widget = QHBoxLayout()
            row_widget.setSpacing(4)
            row_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            for letter in row:
                btn = QPushButton(letter)
                btn.setObjectName("key")
                btn.clicked.connect(lambda _, l=letter: self._callback(l))
                row_widget.addWidget(btn)
            layout.addLayout(row_widget)


# ─── Главное окно ─────────────────────────────────────────────────────────────

class EnigmaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENIGMA SIMULATOR")
        self.setMinimumWidth(680)
        self.setStyleSheet(STYLE)

        self._build_toolbar()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        central = QWidget()
        central.setObjectName("central")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        main_layout.addWidget(self._build_output_section())
        main_layout.addWidget(self._build_rotors_section())
        main_layout.addWidget(self._build_lampboard_section())
        main_layout.addWidget(self._build_keyboard_section())
        main_layout.addWidget(self._build_plugboard_section())
        main_layout.addLayout(self._build_bottom_buttons())

        scroll.setWidget(central)
        self.setCentralWidget(scroll)

    # ── Тулбар ──────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        title = QLabel("  ENIGMA SIMULATOR")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setStyleSheet("letter-spacing:2px;")
        toolbar.addWidget(title)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        for icon in ("🔍", "⚙️", "⛶", "ℹ"):
            btn = QPushButton(icon)
            btn.setObjectName("toolBtn")
            toolbar.addWidget(btn)

        self.addToolBar(toolbar)

    # ── Секция вывода ────────────────────────────────────────────────────────

    def _build_output_section(self) -> QFrame:
        frame, layout = self._make_section("OUTPUT DISPLAY")

        self.output_display = QTextEdit()
        self.output_display.setObjectName("outputDisplay")
        self.output_display.setPlaceholderText("ENCRYPTED TEXT WILL APPEAR HERE...")
        self.output_display.setReadOnly(True)
        self.output_display.setFixedHeight(90)
        layout.addWidget(self.output_display)

        return frame

    # ── Секция роторов ───────────────────────────────────────────────────────

    def _build_rotors_section(self) -> QFrame:
        frame, layout = self._make_section("ROTORS CONFIGURATION")

        rotor_layout = QHBoxLayout()
        rotor_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        rotor_layout.setSpacing(32)

        self.rotor_i   = RotorWidget("ROTOR I",   "B")
        self.rotor_ii  = RotorWidget("ROTOR II",  "B")
        self.rotor_iii = RotorWidget("ROTOR III", "B")

        for r in (self.rotor_i, self.rotor_ii, self.rotor_iii):
            rotor_layout.addWidget(r)

        layout.addLayout(rotor_layout)
        return frame

    # ── Лампборд ────────────────────────────────────────────────────────────

    def _build_lampboard_section(self) -> QFrame:
        frame, layout = self._make_section("LAMPBOARD")
        self.lampboard = LampboardWidget()
        layout.addWidget(self.lampboard)
        return frame

    # ── Клавиатура ───────────────────────────────────────────────────────────

    def _build_keyboard_section(self) -> QFrame:
        frame, layout = self._make_section("KEYBOARD")
        self.keyboard = KeyboardWidget(self._on_key_pressed)
        layout.addWidget(self.keyboard)
        return frame

    # ── Plugboard ────────────────────────────────────────────────────────────

    def _build_plugboard_section(self) -> QFrame:
        frame, layout = self._make_section("PLUGBOARD SETTINGS")

        add_btn = QPushButton("+ ADD CONNECTION")
        add_btn.setObjectName("addConnection")
        add_btn.clicked.connect(self._on_add_connection)
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.plugboard_display = QTextEdit()
        self.plugboard_display.setObjectName("plugboardDisplay")
        self.plugboard_display.setReadOnly(True)
        self.plugboard_display.setFixedHeight(80)
        layout.addWidget(self.plugboard_display)

        return frame

    # ── Нижние кнопки ────────────────────────────────────────────────────────

    def _build_bottom_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        for label, slot in (
            ("RESET", self._on_reset),
            ("CLEAR", self._on_clear),
            ("SAVE CONFIG", self._on_save_config),
        ):
            btn = QPushButton(label)
            btn.setObjectName("bottomBtn")
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        return layout

    # ── Хелпер для секций ────────────────────────────────────────────────────

    @staticmethod
    def _make_section(title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("section")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)

        return frame, layout

    # ── Обработчики событий (заглушки) ───────────────────────────────────────

    def _on_key_pressed(self, letter: str):
        """Нажата клавиша на клавиатуре — здесь будет логика шифрования."""
        # TODO: пропустить букву через роторы и plugboard
        self.lampboard.reset_lights()
        self.lampboard.light_up(letter)
        current = self.output_display.toPlainText()
        self.output_display.setPlainText(current + letter)

    def _on_add_connection(self):
        """Добавить пару в plugboard."""
        # TODO: открыть диалог выбора букв
        pass

    def _on_reset(self):
        """Сбросить всё в начальное состояние."""
        self.output_display.clear()
        self.lampboard.reset_lights()
        self.plugboard_display.clear()

    def _on_clear(self):
        """Очистить только поле вывода."""
        self.output_display.clear()
        self.lampboard.reset_lights()

    def _on_save_config(self):
        """Сохранить конфигурацию."""
        # TODO: сохранить позиции роторов и plugboard в файл
        pass


# ─── Точка входа ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = EnigmaWindow()
    window.show()
    sys.exit(app.exec())
