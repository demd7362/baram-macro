import json
import math
import os
import random
import sys
import time
from pathlib import Path

import keyboard
import pydirectinput
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QSystemTrayIcon, QMenu, QStyle, QHBoxLayout, QFrame, QDoubleSpinBox
)

key_map = {
    # Function keys
    16777264: 'f1', 16777265: 'f2', 16777266: 'f3', 16777267: 'f4',
    16777268: 'f5', 16777269: 'f6', 16777270: 'f7', 16777271: 'f8',
    16777272: 'f9', 16777273: 'f10', 16777274: 'f11', 16777275: 'f12',

    # Special keys
    16777216: 'esc', 16777217: 'tab', 16777220: 'enter', 16777221: 'enter',
    16777223: 'backspace', 16777219: 'del', 16777234: 'left',
    16777236: 'right', 16777235: 'up', 16777237: 'down', 16777232: 'home',
    16777233: 'end', 16777238: 'pageup', 16777239: 'pagedown',
    16777222: 'insert', 16777252: 'capslock', 16777248: 'shift',
    16777249: 'ctrl', 16777251: 'alt', 32: 'space',
}

# 키 설정 정보
keys = {
    'macro_key': {
        'name': '매크로 실행',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    'pilsal': {
        'name': '필살',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    'dongdongju': {
        'name': '동동주',
        'label': None,
        'keys': [],
        'button': None,
        'required': True
    },
}

SETTINGS_FILE = Path('./pilsal_settings.json')
MACRO_NAME = '필살 헬퍼'
available_alphabet_keys = set([chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)])  # a ~ Z
delay = 0.05  # Default delay value
# Asset paths
ICON = Path(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'pilsal.png'))
GITHUB_ICON = Path(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'github_icon.png'))


class StyleSheet:
    MAIN_WINDOW = """
        QMainWindow {
            background-color: #f8f9fa;
        }
    """

    TITLE_LABEL = """
        QLabel {
            font-size: 12px;
            font-weight: bold;
            color: #212529;
            padding: 5px;
        }
    """

    GITHUB_BUTTON = """
        QPushButton {
            border: none;
            border-radius: 4px;
            padding: 8px;
            background-color: transparent;
        }
        QPushButton:hover {
            background-color: #e9ecef;
        }
    """

    SETTINGS_FRAME = """
        QFrame {
            background-color: #ffffff;
            border-radius: 6px;
            padding: 10px;
            border: 1px solid #e9ecef;
        }
    """

    KEY_FRAME = """
        QFrame {
            background-color: #ffffff;
            border-radius: 6px;
            padding: 10px;
            border: 1px solid #e9ecef;
        }
    """

    BUTTON = """
        QPushButton {
            background-color: #228be6;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 120px;
        }
        QPushButton:hover {
            background-color: #1c7ed6;
        }
        QPushButton:pressed {
            background-color: #1971c2;
        }
        QPushButton:disabled {
            background-color: #adb5bd;
        }
    """

    KEY_LABEL = """
        QLabel {
            color: #495057;
            font-size: 14px;
            padding: 5px;
        }
    """

    STATUS_LABEL = """
        QLabel {
            color: #495057;
            font-size: 14px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 4px;
        }
    """

    DELAY_LABEL = """
        QLabel {
            color: #495057;
            font-size: 14px;
        }
    """

    SPINBOX = """
        QDoubleSpinBox {
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 5px;
            min-width: 80px;
        }
        QDoubleSpinBox:hover {
            border-color: #228be6;
        }
        QDoubleSpinBox:focus {
            border-color: #228be6;
            outline: none;
        }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
            border: none;
            background-color: #f8f9fa;
            width: 16px;
        }
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #e9ecef;
        }
    """


def convert_key_code_to_text(key_code):
    return key_map.get(key_code, '')


def save_settings():
    settings = {}
    for key, value in keys.items():
        if key == 'dongdongju':
            settings[key] = {'keys': value['keys']}
        else:
            settings[key] = {'key': value['key']}

    settings['delay'] = delay

    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_settings():
    global delay
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        for key, value in settings.items():
            if key == 'delay':
                delay = float(value)
            elif key in keys:
                if key == 'dongdongju':
                    keys[key]['keys'] = value.get('keys', [])
                    if keys[key]['keys']:
                        keys[key]['label'].setText(f'{keys[key]["name"]} 키: {", ".join(keys[key]["keys"])}')
                else:
                    keys[key]['key'] = value.get('key')
                    if keys[key]['key']:
                        keys[key]['label'].setText(f'{keys[key]["name"]} 키: {keys[key]["key"]}')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.waiting_for_key = None
        self.init_ui()
        load_settings()
        self.init_tray()
        self.setup_global_hotkey()

    def init_ui(self):
        global delay
        self.setWindowTitle(MACRO_NAME)
        self.setFixedSize(450, 600)  # 창 크기 고정
        self.setStyleSheet(StyleSheet.MAIN_WINDOW)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_layout = QVBoxLayout()
        title_label = QLabel('매크로 실행 키로 토글on 후 필 누르세요.\n필 꾹 누르지마세요.\n동동주는 가능한 많이 등록해두세요.\n당연히 막걸리도 가능합니다.')
        title_label.setStyleSheet(StyleSheet.TITLE_LABEL)
        title_layout.addWidget(title_label)
        header_layout.addLayout(title_layout)

        github_button = QPushButton()
        github_button.setStyleSheet(StyleSheet.GITHUB_BUTTON)
        github_button.setToolTip("GitHub 저장소 방문")
        github_button.setIcon(QIcon(str(GITHUB_ICON)))
        github_button.setIconSize(QSize(28, 28))
        github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/demd7362/baram-macro")))
        header_layout.addWidget(github_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addWidget(header_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e9ecef;")
        main_layout.addWidget(separator)

        settings_container = QFrame()
        settings_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)

        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setSpacing(15)

        delay_frame = QFrame()
        delay_frame.setStyleSheet(StyleSheet.SETTINGS_FRAME)
        delay_layout = QHBoxLayout(delay_frame)
        delay_layout.setSpacing(15)

        delay_label = QLabel("딜레이 설정 (초)")
        delay_label.setStyleSheet(StyleSheet.DELAY_LABEL)

        self.delay_spinbox = QDoubleSpinBox()
        self.delay_spinbox.setStyleSheet(StyleSheet.SPINBOX)
        self.delay_spinbox.setRange(0.01, 1.0)
        self.delay_spinbox.setSingleStep(0.01)
        self.delay_spinbox.setValue(delay)
        self.delay_spinbox.valueChanged.connect(self.update_delay)

        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spinbox)
        delay_layout.addStretch()  # 오른쪽 여백을 위한 stretch 추가

        settings_layout.addWidget(delay_frame)

        for key, value in keys.items():
            key_frame = QFrame()
            key_frame.setStyleSheet(StyleSheet.KEY_FRAME)
            key_layout = QHBoxLayout(key_frame)
            key_layout.setSpacing(15)

            value['button'] = QPushButton(f'{value["name"]} 키 설정')
            value['button'].setStyleSheet(StyleSheet.BUTTON)
            value['button'].clicked.connect(lambda checked, k=key: self.start_key_binding(k))

            value['label'] = QLabel(f'{value["name"]} 키: 미설정')
            value['label'].setStyleSheet(StyleSheet.KEY_LABEL)

            key_layout.addWidget(value['button'])
            key_layout.addWidget(value['label'], 1)

            settings_layout.addWidget(key_frame)

        main_layout.addWidget(settings_container)

        self.status_label = QLabel('버튼을 눌러 키를 설정하세요.')
        self.status_label.setStyleSheet(StyleSheet.STATUS_LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(str(ICON)) if ICON.exists() else self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()
        show_action = tray_menu.addAction("보이기")
        quit_action = tray_menu.addAction("종료")

        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def setup_global_hotkey(self):
        macro_key = keys['macro_key']['key']
        if macro_key:
            keyboard.on_press_key(macro_key, lambda _: self.toggle_macro())
            self.status_label.setText(f'매크로 실행 키가 {macro_key}로 설정되었습니다.')

    def toggle_macro(self):
        if not keys['pilsal']['key']:
            self.status_label.setText('필살기 키가 설정되지 않았습니다.')
            return

        self.is_running = not self.is_running
        if self.is_running:
            pilsal_key = keys['pilsal']['key']
            if pilsal_key:
                keyboard.on_press_key(pilsal_key, lambda _: self.use_dongdongju())
            self.status_label.setText('매크로 실행중...')
            set_button_enabled(False)
            self.tray_icon.showMessage(MACRO_NAME, "매크로 실행", QSystemTrayIcon.Information, 2000)
        else:
            pilsal_key = keys['pilsal']['key']
            print(pilsal_key)
            keyboard.unhook_key(pilsal_key)
            self.status_label.setText('매크로가 중지되었습니다.')
            set_button_enabled(True)
            self.tray_icon.showMessage(MACRO_NAME, "매크로 중지", QSystemTrayIcon.Information, 2000)

    def update_delay(self, value):
        global delay
        delay = value
        save_settings()

    def use_dongdongju(self):
        global delay
        dongdongju_keys = keys['dongdongju']['keys']
        if dongdongju_keys:
            index = math.floor(random.random() * len(dongdongju_keys))
            pydirectinput.press('u')
            time.sleep(delay)
            pydirectinput.press(dongdongju_keys[index])
            time.sleep(delay)
            pydirectinput.press('u')
            time.sleep(delay)
            pydirectinput.press(dongdongju_keys[index])

    def keyPressEvent(self, event):
        if not self.waiting_for_key:
            return
        key_code = event.key()
        key_text = event.text()
        if not key_text:
            key_text = convert_key_code_to_text(key_code)
        if event.key() == Qt.Key_Escape:
            set_button_enabled(True)
            if self.waiting_for_key != 'dongdongju':
                keys[self.waiting_for_key]['key'] = None
                keys[self.waiting_for_key]['label'].setText(f'{keys[self.waiting_for_key]["name"]} 키: 미설정')
            self.waiting_for_key = None
            self.status_label.setText('버튼을 눌러 키를 설정하세요.')
            save_settings()
            return

        if self.waiting_for_key == 'dongdongju':
            if key_text == '1':
                keys[self.waiting_for_key]['keys'] = []
                keys[self.waiting_for_key]['label'].setText(f'{keys[self.waiting_for_key]["name"]} 키: 미설정')
                self.status_label.setText('동동주 키를 입력해주세요. 여러 개 입력 가능합니다. ESC로 설정을 종료합니다. 1 입력 시 초기화됩니다.')
                save_settings()
                return
            elif key_text not in available_alphabet_keys:
                self.status_label.setText('동동주 키는 알파벳만 입력 가능합니다.')
                return

        elif self.waiting_for_key == 'pilsal':
            if not 48 <= event.key() <= 57:
                self.status_label.setText('숫자만 입력 가능합니다.')
                return

        # 동동주 키는 여러 개 설정 가능
        if self.waiting_for_key == 'dongdongju':
            if key_text not in keys['dongdongju']['keys']:
                keys['dongdongju']['keys'].append(key_text)
                keys['dongdongju']['label'].setText(
                    f'{keys["dongdongju"]["name"]} 키: {", ".join(keys["dongdongju"]["keys"])}')
                self.status_label.setText(f'동동주 키가 추가되었습니다! (현재: {", ".join(keys["dongdongju"]["keys"])})')
        else:
            # 키 중복 체크 (동동주 키 제외)
            for key, value in keys.items():
                if key != 'dongdongju':
                    if value.get('key') == key_text and self.waiting_for_key != key:
                        self.status_label.setText(f'{value["name"]}에 이미 설정된 키입니다.')
                        return

            keys[self.waiting_for_key]['key'] = key_text
            keys[self.waiting_for_key]['label'].setText(f'{keys[self.waiting_for_key]["name"]} 키: {key_text}')
            set_button_enabled(True)

            if self.waiting_for_key == 'macro_key':
                self.setup_global_hotkey()
            else:
                self.status_label.setText(f'{keys[self.waiting_for_key]["name"]} 키가 설정되었습니다!')

            self.waiting_for_key = None

        save_settings()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(MACRO_NAME, "프로그램이 시스템 트레이로 최소화되었습니다.",
                                       QSystemTrayIcon.Information, 2000)
            event.ignore()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def quit_application(self):
        if self.macro_worker.is_running:
            self.macro_worker.stop()
            self.macro_worker.wait()
        keyboard.unhook_all()
        save_settings()
        QApplication.quit()

    def start_key_binding(self, key):
        self.waiting_for_key = key
        if key == 'dongdongju':
            self.status_label.setText('동동주 키를 입력해주세요. 여러 개 입력 가능합니다. ESC로 설정을 종료합니다. 1 입력 시 초기화됩니다.')
        else:
            self.status_label.setText('키를 입력해주세요. 취소하려면 ESC 버튼을 누르세요.')
        set_button_enabled(False)


def set_button_enabled(is_enabled):
    for value in keys.values():
        value['button'].setEnabled(is_enabled)


def main():
    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print('시스템 트레이를 지원하지 않는 시스템입니다.')
        sys.exit(1)

    app.setStyle('Fusion')

    if ICON.exists():
        app.setWindowIcon(QIcon(str(ICON)))

    QApplication.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    pydirectinput.PAUSE = 0.01
    pydirectinput.FAILSAFE = False
    main()
