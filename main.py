import sys
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QScrollArea,
    QDialog, QLineEdit, QDialogButtonBox, QMessageBox,
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRect

from back.enigma import EnigmaMachine


KEYBOARD_ROWS = ["QWERTZUIO", "ASDFGHJK", "PYXCVBNML"]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CONFIG_FILE = Path(__file__).parent / "enigma_config.json"

BG          = "#e0e0e0"
CARD_BG     = "#f0f0f0"
BORDER_CLR  = "#c0c0c0"
TEXT_CLR    = "#222222"
MUTED_CLR   = "#888888"
WHITE       = "#ffffff"


# ── Lamp widget ───────────────────────────────────────────────────────────────

class LampWidget(QWidget):
    """Circular lamp indicator (letter label above, circle below)."""

    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.lit = False
        self.setFixedSize(42, 48)

    def set_lit(self, on: bool):
        if self.lit != on:
            self.lit = on
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        circle = QRect(6, 16, 28, 28)
        if self.lit:
            p.setBrush(QBrush(QColor(235, 195, 15)))
            p.setPen(QPen(QColor(150, 110, 0), 1.5))
        else:
            p.setBrush(QBrush(QColor(208, 208, 208)))
            p.setPen(QPen(QColor(150, 150, 150), 1))
        p.drawEllipse(circle)
        p.setPen(QColor(70, 70, 70))
        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        p.drawText(QRect(0, 2, 42, 14), Qt.AlignmentFlag.AlignCenter, self.letter)


# ── Rotor display ─────────────────────────────────────────────────────────────

class RotorDisplay(QWidget):
    """Three-letter scroll window (prev / current / next) with ▲▼ buttons."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._pos = 0
        self._callback = None
        self._build(title)

    def _build(self, title: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        hdr = QLabel(title)
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setFont(QFont("Courier New", 8))
        hdr.setStyleSheet(f"color:{MUTED_CLR}; letter-spacing:2px; border:none; background:transparent;")
        layout.addWidget(hdr)

        dim = f"QLabel{{border:1px solid {BORDER_CLR}; background:#e8e8e8; color:{MUTED_CLR};}}"
        sel = f"QLabel{{border:2px solid {TEXT_CLR}; background:{WHITE}; color:{TEXT_CLR}; font-weight:bold;}}"
        btn_css = (
            f"QPushButton{{border:1px solid {BORDER_CLR}; background:#e8e8e8; font-size:10px;}}"
            f"QPushButton:pressed{{background:#ccc;}}"
        )

        self.top = QLabel()
        self.top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top.setFixedSize(44, 34)
        self.top.setFont(QFont("Courier New", 13))
        self.top.setStyleSheet(dim)

        self.mid = QLabel()
        self.mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mid.setFixedSize(44, 44)
        self.mid.setFont(QFont("Courier New", 17, QFont.Weight.Bold))
        self.mid.setStyleSheet(sel)

        self.bot = QLabel()
        self.bot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bot.setFixedSize(44, 34)
        self.bot.setFont(QFont("Courier New", 13))
        self.bot.setStyleSheet(dim)

        for w in [self.top, self.mid, self.bot]:
            layout.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)
        self.up_btn = QPushButton("▲")
        self.dn_btn = QPushButton("▼")
        for b in [self.up_btn, self.dn_btn]:
            b.setFixedSize(40, 26)
            b.setStyleSheet(btn_css)
        self.up_btn.clicked.connect(self._inc)
        self.dn_btn.clicked.connect(self._dec)
        btn_row.addWidget(self.up_btn)
        btn_row.addWidget(self.dn_btn)
        layout.addLayout(btn_row)

        self._refresh()

    def _inc(self):
        self._pos = (self._pos + 1) % 26
        self._refresh()
        if self._callback:
            self._callback()

    def _dec(self):
        self._pos = (self._pos - 1) % 26
        self._refresh()
        if self._callback:
            self._callback()

    def _refresh(self):
        self.top.setText(ALPHABET[(self._pos + 1) % 26])
        self.mid.setText(ALPHABET[self._pos])
        self.bot.setText(ALPHABET[(self._pos - 1) % 26])

    def get_letter(self) -> str:
        return ALPHABET[self._pos]

    def set_position(self, letter: str):
        self._pos = ord(letter.upper()) - ord("A")
        self._refresh()

    def on_change(self, fn):
        self._callback = fn


# ── Plugboard dialog ──────────────────────────────────────────────────────────

class AddConnectionDialog(QDialog):
    """Minimal dialog to enter two letters for a plugboard cable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Plugboard Connection")
        self.setFixedSize(300, 140)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel("Enter two letters to connect (e.g. A B):")
        hint.setFont(QFont("Courier New", 9))
        layout.addWidget(hint)

        self.input = QLineEdit()
        self.input.setMaxLength(3)
        self.input.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input.setPlaceholderText("A B")
        layout.addWidget(self.input)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_pair(self) -> tuple[str, str] | None:
        text = self.input.text().upper().replace(" ", "")
        if len(text) == 2 and text[0].isalpha() and text[1].isalpha():
            return text[0], text[1]
        return None


# ── Main window ───────────────────────────────────────────────────────────────

class EnigmaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENIGMA SIMULATOR")
        self.setMinimumWidth(660)
        self.setMinimumHeight(700)

        self._machine = EnigmaMachine(
            rotor_names=["I", "II", "III"],
            reflector_name="UKW-B",
            ring_settings=[1, 1, 1],
            start_positions=["A", "A", "A"],
        )
        self._lamps: dict[str, LampWidget] = {}
        self._rotors: list[RotorDisplay] = []
        self._lit_lamp: str | None = None

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _card(self, label: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{CARD_BG}; border:1px solid {BORDER_CLR};}}"
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(12, 8, 12, 12)
        vbox.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFont(QFont("Courier New", 8))
        lbl.setStyleSheet(
            f"color:{MUTED_CLR}; letter-spacing:2px; border:none; background:transparent;"
        )
        vbox.addWidget(lbl)
        return frame, vbox

    def _build_ui(self):
        # Header bar
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background:{WHITE}; border-bottom:1px solid {BORDER_CLR};")
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(16, 0, 12, 0)

        title = QLabel("ENIGMA SIMULATOR")
        title.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color:{TEXT_CLR}; letter-spacing:3px; border:none; background:transparent;"
        )
        h_row.addWidget(title)
        h_row.addStretch()

        icon_css = (
            f"QPushButton{{border:1px solid {BORDER_CLR}; background:{WHITE}; "
            f"font-size:14px; color:{MUTED_CLR};}}"
            f"QPushButton:hover{{background:#eee;}}"
        )
        for icon in ["⌕", "⚙", "⤢", "ⓘ"]:
            btn = QPushButton(icon)
            btn.setFixedSize(34, 34)
            btn.setStyleSheet(icon_css)
            h_row.addWidget(btn)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background:{BG};")

        content = QWidget()
        content.setStyleSheet(f"background:{BG};")
        main = QVBoxLayout(content)
        main.setSpacing(10)
        main.setContentsMargins(14, 14, 14, 14)

        main.addWidget(self._build_output())
        main.addWidget(self._build_rotors())
        main.addWidget(self._build_lampboard())
        main.addWidget(self._build_keyboard())
        main.addWidget(self._build_plugboard())
        main.addWidget(self._build_bottom_row())

        scroll.setWidget(content)

        central = QWidget()
        central.setStyleSheet(f"background:{BG};")
        cv = QVBoxLayout(central)
        cv.setSpacing(0)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.addWidget(header)
        cv.addWidget(scroll)
        self.setCentralWidget(central)

    def _build_output(self) -> QFrame:
        frame, vbox = self._card("OUTPUT DISPLAY")
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("ENCRYPTED TEXT WILL APPEAR HERE...")
        self.output.setMinimumHeight(90)
        self.output.setFont(QFont("Courier New", 13))
        self.output.setStyleSheet(
            f"QTextEdit{{border:1px solid {BORDER_CLR}; background:{WHITE}; color:{TEXT_CLR};}}"
        )
        vbox.addWidget(self.output)
        return frame

    def _build_rotors(self) -> QFrame:
        frame, vbox = self._card("ROTORS CONFIGURATION")
        row = QHBoxLayout()
        row.setSpacing(30)
        row.addStretch()
        for i, name in enumerate(["ROTOR I", "ROTOR II", "ROTOR III"]):
            rd = RotorDisplay(name)
            rd.on_change(lambda i=i: self._rotor_changed(i))
            self._rotors.append(rd)
            row.addWidget(rd)
        row.addStretch()
        vbox.addLayout(row)
        return frame

    def _build_lampboard(self) -> QFrame:
        frame, vbox = self._card("LAMPBOARD")
        for key_row in KEYBOARD_ROWS:
            row = QHBoxLayout()
            row.setSpacing(4)
            row.addStretch()
            for ch in key_row:
                lamp = LampWidget(ch)
                self._lamps[ch] = lamp
                row.addWidget(lamp)
            row.addStretch()
            vbox.addLayout(row)
        return frame

    def _build_keyboard(self) -> QFrame:
        frame, vbox = self._card("KEYBOARD")
        key_css = (
            f"QPushButton{{border:1px solid {BORDER_CLR}; background:{WHITE}; "
            f"color:{TEXT_CLR}; font-family:'Courier New'; font-size:13px; font-weight:bold;}}"
            f"QPushButton:pressed{{background:#d8d8d8;}}"
        )
        for key_row in KEYBOARD_ROWS:
            row = QHBoxLayout()
            row.setSpacing(4)
            row.addStretch()
            for ch in key_row:
                btn = QPushButton(ch)
                btn.setFixedSize(46, 46)
                btn.setStyleSheet(key_css)
                btn.clicked.connect(lambda checked, c=ch: self._press_key(c))
                row.addWidget(btn)
            row.addStretch()
            vbox.addLayout(row)
        return frame

    def _build_plugboard(self) -> QFrame:
        frame, vbox = self._card("PLUGBOARD SETTINGS")

        add_btn = QPushButton("+ ADD CONNECTION")
        add_btn.setFixedSize(200, 36)
        add_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        add_btn.setStyleSheet(
            f"QPushButton{{border:1px solid {BORDER_CLR}; background:{WHITE}; "
            f"color:{TEXT_CLR}; letter-spacing:1px;}}"
            f"QPushButton:pressed{{background:#e0e0e0;}}"
        )
        add_btn.clicked.connect(self._add_connection)
        vbox.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.plugboard_display = QTextEdit()
        self.plugboard_display.setReadOnly(True)
        self.plugboard_display.setFixedHeight(80)
        self.plugboard_display.setFont(QFont("Courier New", 11))
        self.plugboard_display.setStyleSheet(
            f"QTextEdit{{border:1px solid {BORDER_CLR}; background:{WHITE}; color:#444;}}"
        )
        vbox.addWidget(self.plugboard_display)
        return frame

    def _build_bottom_row(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background:transparent;")
        row = QHBoxLayout(widget)
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        btn_css = (
            f"QPushButton{{border:1px solid {BORDER_CLR}; background:{WHITE}; "
            f"color:{TEXT_CLR}; font-family:'Courier New'; font-size:10px; "
            f"font-weight:bold; letter-spacing:2px;}}"
            f"QPushButton:pressed{{background:#d8d8d8;}}"
        )
        for label, slot in [
            ("RESET", self._reset),
            ("CLEAR", self._clear),
            ("SAVE CONFIG", self._save_config),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setStyleSheet(btn_css)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        return widget

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _rotor_changed(self, idx: int):
        positions = [rd.get_letter() for rd in self._rotors]
        self._machine.reset(positions)

    def _press_key(self, char: str):
        if self._lit_lamp is not None:
            self._lamps[self._lit_lamp].set_lit(False)
            self._lit_lamp = None

        result, _ = self._machine._encode_letter(char)
        self.output.insertPlainText(result)

        if result in self._lamps:
            self._lamps[result].set_lit(True)
            self._lit_lamp = result

        for i, rd in enumerate(self._rotors):
            rd.set_position(self._machine.get_rotor_positions()[i])

    def _add_connection(self):
        dlg = AddConnectionDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        pair = dlg.get_pair()
        if pair is None:
            QMessageBox.warning(self, "Invalid Input", "Enter exactly two different letters.")
            return
        try:
            self._machine.plugboard.add_connection(*pair)
            pairs = self._machine.get_plugboard_pairs()
            self.plugboard_display.setPlainText(
                "  ".join(f"{a} ↔ {b}" for a, b in pairs)
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Connection Error", str(exc))

    def _reset(self):
        self._machine = EnigmaMachine(
            rotor_names=["I", "II", "III"],
            reflector_name="UKW-B",
            ring_settings=[1, 1, 1],
            start_positions=["A", "A", "A"],
        )
        for rd in self._rotors:
            rd.set_position("A")
        if self._lit_lamp is not None:
            self._lamps[self._lit_lamp].set_lit(False)
            self._lit_lamp = None
        self.output.clear()
        self.plugboard_display.clear()

    def _clear(self):
        self.output.clear()
        if self._lit_lamp is not None:
            self._lamps[self._lit_lamp].set_lit(False)
            self._lit_lamp = None

    def _save_config(self):
        config = {
            "rotor_positions": [rd.get_letter() for rd in self._rotors],
            "plugboard": self._machine.get_plugboard_pairs(),
        }
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        QMessageBox.information(self, "Saved", f"Config saved to {CONFIG_FILE.name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnigmaWindow()
    window.show()
    sys.exit(app.exec())
