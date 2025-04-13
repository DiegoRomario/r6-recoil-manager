import sys
import re
import psutil
import subprocess
import json
import os
from PyQt5 import QtWidgets, QtCore

# === Operator config ===
OPERATORS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'operators.json')

with open(OPERATORS_JSON_PATH, 'r', encoding='utf-8') as f:
    OPERATORS = json.load(f)

# Ensure [none] is present
none_operator = {
    "X": 0,
    "Y": 0,
    "GRIP": "N/A",
    "BARREL": "N/A",
    "SIGHTS": "N/A"
}

for role in ["attackers", "defenders"]:
    if "[none]" not in OPERATORS[role]:
        OPERATORS[role] = {"[none]": none_operator, **OPERATORS[role]}

LUA_SCRIPT_PATH = r""
GHUB_TRAY_PATH = r"C:\Program Files\LGHUB\system_tray\lghub_system_tray.exe"

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.is_minimized = False
        self.drag_pos = None

        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.init_ui()
        self.show_full_ui()
        self.move_to_bottom_left()
        self.apply_clicked()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(219, 227, 246, 0.9);
                border-radius: 12px;
                font-size: 10pt;
            }
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 6px;
            }
            QRadioButton, QComboBox, QLabel {
                padding: 2px;
            }
        """)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        top_bar = QtWidgets.QHBoxLayout()
        top_bar.addStretch()

        self.btn_min = QtWidgets.QPushButton("–")
        self.btn_min.setFixedSize(24, 24)
        self.btn_min.clicked.connect(self.toggle_minimize)

        self.btn_close = QtWidgets.QPushButton("x")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.clicked.connect(QtWidgets.QApplication.quit)

        top_bar.addWidget(self.btn_min)
        top_bar.addWidget(self.btn_close)

        self.main_layout.addLayout(top_bar)

        self.radio_attackers = QtWidgets.QRadioButton("Attackers")
        self.radio_defenders = QtWidgets.QRadioButton("Defenders")
        self.radio_attackers.setChecked(True)
        self.radio_attackers.toggled.connect(self.update_operators)

        self.main_layout.addWidget(self.radio_attackers)
        self.main_layout.addWidget(self.radio_defenders)

        self.combo = QtWidgets.QComboBox()
        self.main_layout.addWidget(self.combo)
        self.update_operators()

        self.button = QtWidgets.QPushButton("Apply Configuration")
        self.button.clicked.connect(self.apply_clicked)
        self.main_layout.addWidget(self.button)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        self.main_layout.addWidget(self.status_label)

        self.main_layout.addStretch()

        self.controls_container = QtWidgets.QWidget()
        self.controls_container.setLayout(self.main_layout)

        self.minimized_button = QtWidgets.QPushButton("☰")
        self.minimized_button.setFixedSize(40, 40)
        self.minimized_button.clicked.connect(self.toggle_minimize)
        self.minimized_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(219, 227, 246, 0.8);
                border: none;
                font-size: 14pt;
                border-radius: 10px;
            }
        """)
        self.minimized_button.setToolTip("Click to restore overlay")
        self.minimized_button.hide()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.controls_container)
        self.layout.addWidget(self.minimized_button)
        self.setLayout(self.layout)

    def toggle_minimize(self):
        if self.is_minimized:
            self.show_full_ui()
        else:
            self.show_minimized_ui()

    def show_full_ui(self):
        self.setFixedSize(200, 280)
        self.controls_container.show()
        self.minimized_button.hide()
        self.is_minimized = False

    def show_minimized_ui(self):
        self.setFixedSize(50, 50)
        self.controls_container.hide()
        self.minimized_button.show()
        self.is_minimized = True

    def update_operators(self):
        self.combo.clear()
        role = "attackers" if self.radio_attackers.isChecked() else "defenders"
        self.combo.addItems(OPERATORS[role].keys())
        index = self.combo.findText("[none]")
        if index != -1:
            self.combo.setCurrentIndex(index)

    def restart_ghub(self):
        ghub_processes = ["lghub.exe", "lghub_agent.exe", "lghub_updater.exe", "lghub_system_tray.exe"]
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].lower() in ghub_processes:
                try:
                    print(f"[✖] Terminating {proc.info['name']}")
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception as e:
                    print(f"[!] Error terminating {proc.info['name']}: {e}")

    def apply_clicked(self):
        operator = self.combo.currentText()
        role = "attackers" if self.radio_attackers.isChecked() else "defenders"
        config = OPERATORS[role][operator]
        x = config["X"]
        y = config["Y"]
        grip = config.get("GRIP", "N/A")
        barrel = config.get("BARREL", "N/A")
        sights = config.get("SIGHTS", "N/A")

        print(f"[Apply] Selected operator: {operator}")
        print(f"Recoil Config: X = {x}, Y = {y}")
        print(f"Weapon Config: GRIP = {grip}, BARREL = {barrel}, SIGHTS = {sights}")

        self.radio_attackers.setEnabled(False)
        self.radio_defenders.setEnabled(False)
        self.combo.setEnabled(False)
        self.button.setEnabled(False)

        if operator == "[none]":
            self.status_label.setText("♻️ Resetting recoil control...")
        else:
            self.status_label.setText("⌛️ Applying recoil control...")

        try:
            with open(LUA_SCRIPT_PATH, "r", encoding="utf-8") as file:
                content = file.read()

            content = re.sub(r"HorizontalRecoilCompensation\s*=\s*-?\d+", f"HorizontalRecoilCompensation = {x}", content)
            content = re.sub(r"VerticalRecoilCompensation\s*=\s*-?\d+", f"VerticalRecoilCompensation = {y}", content)

            with open(LUA_SCRIPT_PATH, "w", encoding="utf-8") as file:
                file.write(content)

            print("[✓] Lua script updated successfully.")
        except Exception as e:
            print(f"[✗] Failed to update Lua script: {e}")
            self.status_label.setText("Failed to update script.")
            return

        self.restart_ghub()
        try:
            print("[→] Launching G HUB to system tray...")
            subprocess.Popen([GHUB_TRAY_PATH, "--background"], shell=False)
            print("[✓] G HUB started in tray.")
        except Exception as e:  
            print(f"[✗] Failed to launch G HUB in tray: {e}")
            self.status_label.setText("Failed to start G HUB.")
            return

        QtCore.QTimer.singleShot(7000, lambda: self.finish_update(operator, role, x, y, grip, barrel, sights))

    def finish_update(self, operator, role, x, y, grip, barrel, sights):
        emoji_role = "➖" if operator == "[none]" else ("⚔️" if role == "attackers" else "🛡️")
        self.status_label.setText(
            f"{emoji_role} Operator: {operator}\n"
            f"📐 X: {x} | Y: {y}\n"
            f"✊ Grip: {grip}\n"
            f"🔫 Barrel: {barrel}\n"
            f"🔭 Sight: {sights}"
        )

        self.radio_attackers.setEnabled(True)
        self.radio_defenders.setEnabled(True)
        self.combo.setEnabled(True)
        self.button.setEnabled(True)

    def move_to_bottom_left(self):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = 20
        y = screen.height() - self.height() - 40
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self.is_minimized:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.drag_pos and not self.is_minimized:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Overlay()
    window.show()
    sys.exit(app.exec_())
