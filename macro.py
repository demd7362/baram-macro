import json
import os
import sys
import time
from pathlib import Path
from typing import override

import cv2
import keyboard
import numpy
import pyautogui
import pydirectinput
from PyQt5.QtCore import Qt, QThread, QSize, QUrl
from PyQt5.QtGui import QFont, QDesktopServices, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QSystemTrayIcon, QMenu, QStyle, QHBoxLayout, QFrame, QGridLayout, QDoubleSpinBox, QSpinBox
)

# 설정 파일 경로
SETTINGS_FILE = Path('./macro_settings.json')
DEFAULT_DELAY = 0.1
DEFAULT_HEAL_COUNT = 3

MACRO_NAME = '주수리 헬퍼'
# ICON = Path('assets/icon.png')
# GITHUB_ICON = Path('assets/github_icon.png')
# half_mp_template = cv2.imread('assets/half_mp.png', 0)
# half_hp_template = cv2.imread('assets/half_hp.png', 0)
# gongjeung_template = cv2.imread('assets/gongjeung.png', 0)
# dead_template = cv2.imread('assets/dead.png', 0)

ICON = Path(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'icon.png'))
GITHUB_ICON = Path(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'github_icon.png'))
half_mp_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'half_mp.png'), 0)
half_hp_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'half_hp.png'), 0)
gongjeung_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'gongjeung.png'),
                                0)
dead_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'dead.png'), 0)

directions = ['left', 'right', 'up', 'down']


def capture_screen():
    screen = pyautogui.screenshot()
    screen_np = numpy.array(screen)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)

    # 노이즈 제거
    # screen_gray = cv2.GaussianBlur(screen_gray, (3,3), 0)
    #
    # # 대비 향상
    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    # screen_gray = clahe.apply(screen_gray)

    return screen_gray


def analyze_screen(screen_gray, template):
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(f'max_val: {max_val}')
    # 템플릿이 감지된 경우
    return max_val >= 0.9  # 임계값을 조절하여 정확도 설정


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

keys = {
    'macro_key': {
        'name': '매크로 실행',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    # 'attack': {
    #     'name': '신수마법(단일)',
    #     'label': None,
    #     'key': None,
    #     'button': None,
    #     'required': False
    # },
    # 'direction_attack': {
    #     'name': '신수마법(첨)',
    #     'label': None,
    #     'key': None,
    #     'button': None,
    #     'required': False
    # },
    'heal': {
        'name': '반피이하 자동 기원',
        'label': None,
        'key': None,
        'button': None,
        'required': False
    },
    'mana': {
        'name': '공력증강',
        'label': None,
        'key': None,
        'button': None,
        'required': False
    },
    'poison': {
        'name': '중독',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    'curse': {
        'name': '저주',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    'paralyze': {
        'name': '마비',
        'label': None,
        'key': None,
        'button': None,
        'required': True
    },
    'mujang': {
        'name': '무장',
        'label': None,
        'key': None,
        'button': None,
        'required': False
    },
    'boho': {
        'name': '보호',
        'label': None,
        'key': None,
        'button': None,
        'required': False
    },
}


class StyleSheet:
    MAIN_WINDOW = """
        QMainWindow {
            background-color: #f0f0f0;
        }
    """

    BUTTON = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:disabled {
            background-color: #BDBDBD;
        }
    """

    GITHUB_BUTTON = """
        QPushButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: #E0E0E0;
            border-radius: 4px;
        }
    """

    KEY_LABEL = """
        QLabel {
            background-color: white;
            padding: 5px;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
    """

    STATUS_LABEL = """
        QLabel {
            color: #333;
            padding: 10px;
            font-weight: bold;
            background-color: #E3F2FD;
            border-radius: 4px;
        }
    """

    SPINBOX = """
        QSpinBox, QDoubleSpinBox {
            background-color: white;
            padding: 5px;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
        QSpinBox:hover, QDoubleSpinBox:hover {
            border: 1px solid #2196F3;
        }
    """


class MacroWorker(QThread):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.delay = DEFAULT_DELAY
        self.heal_count = DEFAULT_HEAL_COUNT

    def press_home(self):
        keyboard.press_and_release('home')  # pydirectinput home 미작동
        time.sleep(self.delay)

    def run(self):
        heal = keys['heal']['key']
        mana = keys['mana']['key']
        poison = keys['poison']['key']
        curse = keys['curse']['key']
        paralyze = keys['paralyze']['key']
        mujang = keys['mujang']['key']
        boho = keys['boho']['key']
        exit_flag = False

        if mujang:
            pydirectinput.press(mujang)
            self.press_home()
            pydirectinput.press('enter')
            time.sleep(0.05)
        if boho:
            pydirectinput.press(boho)
            self.press_home()
            pydirectinput.press('enter')
            time.sleep(0.05)

        while self.is_running:
            pydirectinput.press(poison)
            pydirectinput.press('up')
            pydirectinput.press('enter')
            time.sleep(self.delay)
            pydirectinput.press(curse)
            pydirectinput.press('enter')
            time.sleep(self.delay)
            pydirectinput.press(paralyze)
            pydirectinput.press('enter')
            time.sleep(self.delay)
            if not heal and not mana:
                continue
            screen_gray = capture_screen()
            if heal:
                is_hp_half = analyze_screen(screen_gray, half_hp_template)
                print(f'체력이 절반인가 {is_hp_half}')
                if is_hp_half:
                    heal_count = 0
                    while heal_count < self.heal_count:
                        pydirectinput.press(heal)
                        self.press_home()
                        pydirectinput.press('enter')
                        heal_count += 1
                        # screen_gray = capture_screen()
                        # is_dead = analyze_screen(screen_gray, dead_template)
                        # if is_dead:
                        #     exit_flag = True
                        #     break
                        # is_hp_half = analyze_screen(screen_gray, half_hp_template)
                        time.sleep(0.1)
                    # if exit_flag:
                    #     break
            if mana:
                is_mp_half = analyze_screen(screen_gray, half_mp_template)
                print(f'마나가 절반인가 {is_mp_half}')
                if is_mp_half:
                    is_gongjeung_success = analyze_screen(screen_gray, half_mp_template)
                    pydirectinput.press(mana)
                    while not is_gongjeung_success:
                        pydirectinput.press(mana)
                        screen_gray = capture_screen()
                        is_dead = analyze_screen(screen_gray, dead_template)
                        if is_dead:
                            exit_flag = True
                            break
                        is_gongjeung_success = analyze_screen(screen_gray, half_mp_template)
                        time.sleep(0.1)
                if exit_flag:
                    break

    def stop(self):
        self.is_running = False


def save_settings():
    settings = {}
    for key, value in keys.items():
        settings[key] = value['key']

    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_settings():
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            for key, value in settings.items():
                if key in keys:
                    keys[key]['key'] = value
                    if value:
                        keys[key]['label'].setText(f'{keys[key]['name']} 키: {value}')
    except Exception as e:
        print(f"Error loading settings: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.heal_count_input = None
        self.delay_input = None
        self.is_running = False
        self.waiting_for_key = None
        self.macro_worker = MacroWorker()
        self.init_ui()
        self.init_tray()
        load_settings()
        self.setup_global_hotkey()

    def init_ui(self):
        self.setWindowTitle(MACRO_NAME)
        self.setGeometry(300, 300, 400, 600)
        self.setStyleSheet(StyleSheet.MAIN_WINDOW)

        # 메인 위젯과 레이아웃
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 상단 타이틀 영역
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 타이틀 레이블
        title_label = QLabel('보무는 실행 시 한번만 겁니다. version 241107')
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        # GitHub 버튼
        github_button = QPushButton()
        github_button.setStyleSheet(StyleSheet.GITHUB_BUTTON)
        github_button.setToolTip("GitHub 저장소 방문")
        github_button.setIcon(QIcon(str(GITHUB_ICON)))  # GitHub 아이콘 설정
        github_button.setIconSize(QSize(24, 24))
        github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/demd7362/jusuri-helper")))
        title_layout.addWidget(github_button, alignment=Qt.AlignRight)

        main_layout.addWidget(title_frame)

        # 키 설정 그리드
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        row = 0

        delay_frame = QFrame()
        delay_layout = QHBoxLayout(delay_frame)
        delay_label = QLabel('스킬 딜레이 (초):')
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setStyleSheet(StyleSheet.SPINBOX)
        self.delay_input.setRange(0.01, 1.0)
        self.delay_input.setSingleStep(0.01)
        self.delay_input.setValue(DEFAULT_DELAY)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_input)
        main_layout.addWidget(delay_frame)

        # Add heal count input
        heal_count_frame = QFrame()
        heal_count_layout = QHBoxLayout(heal_count_frame)
        heal_count_label = QLabel('기원 시전 횟수:')
        self.heal_count_input = QSpinBox()
        self.heal_count_input.setStyleSheet(StyleSheet.SPINBOX)
        self.heal_count_input.setRange(1, 20)
        self.heal_count_input.setValue(DEFAULT_HEAL_COUNT)
        heal_count_layout.addWidget(heal_count_label)
        heal_count_layout.addWidget(self.heal_count_input)
        main_layout.addWidget(heal_count_frame)

        # Add line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 매크로 키는 별도로 처리
        macro_frame = QFrame()
        macro_layout = QHBoxLayout(macro_frame)
        keys['macro_key']['button'] = QPushButton(f'{keys['macro_key']['name']} 키 설정')
        keys['macro_key']['button'].setStyleSheet(StyleSheet.BUTTON)
        keys['macro_key']['button'].clicked.connect(lambda: self.start_key_binding('macro_key'))
        keys['macro_key']['label'] = QLabel(f'{keys['macro_key']['name']} 키: 미설정')
        keys['macro_key']['label'].setStyleSheet(StyleSheet.KEY_LABEL)
        macro_layout.addWidget(keys['macro_key']['button'])
        macro_layout.addWidget(keys['macro_key']['label'])
        main_layout.addWidget(macro_frame)

        # 구분선 추가
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 나머지 키 설정
        for key, value in keys.items():
            if key == 'macro_key':
                continue

            frame = QFrame()
            layout = QHBoxLayout(frame)

            value['button'] = QPushButton(f'{value['name'] + ('[필수]' if value['required'] else '')} 키 설정')
            value['button'].setStyleSheet(StyleSheet.BUTTON)
            value['button'].clicked.connect(lambda checked, k=key: self.start_key_binding(k))

            value['label'] = QLabel(f'{value['name']} 키: 미설정')
            value['label'].setStyleSheet(StyleSheet.KEY_LABEL)

            layout.addWidget(value['button'])
            layout.addWidget(value['label'])

            grid_layout.addWidget(frame, row, 0)
            row += 1

        main_layout.addLayout(grid_layout)

        # 상태 표시 레이블
        self.status_label = QLabel('버튼을 눌러 키를 설정하세요.')
        self.status_label.setStyleSheet(StyleSheet.STATUS_LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.show()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)

        # 트레이 아이콘 설정
        if ICON.exists():
            self.tray_icon.setIcon(QIcon(str(ICON)))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

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
            keyboard.on_press_key(macro_key.lower(), lambda _: self.toggle_macro())
            self.status_label.setText(f'매크로 실행 키가 {macro_key}로 설정되었습니다.')

    def toggle_macro(self):
        for key, value in keys.items():
            if keys[key]['required'] and value['key'] is None:
                self.status_label.setText(f'{value['name']} 키가 등록되지 않았습니다.')
                return

        self.is_running = not self.is_running
        if self.is_running:
            self.macro_worker.delay = self.delay_input.value()
            self.macro_worker.heal_count = self.heal_count_input.value()
            self.status_label.setText('매크로 실행중...')
            set_button_enabled(False)
            self.delay_input.setEnabled(False)
            self.heal_count_input.setEnabled(False)
            self.macro_worker.is_running = True
            self.macro_worker.start()
            self.tray_icon.showMessage(MACRO_NAME, "매크로 실행", QSystemTrayIcon.Information, 2000)
        else:
            self.status_label.setText('매크로가 중지되었습니다.')
            set_button_enabled(True)
            self.delay_input.setEnabled(True)
            self.heal_count_input.setEnabled(True)
            self.macro_worker.stop()
            self.tray_icon.showMessage(MACRO_NAME, "매크로 중지", QSystemTrayIcon.Information, 2000)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    @override
    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                MACRO_NAME,
                "프로그램이 시스템 트레이로 최소화되었습니다.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()

    def quit_application(self):
        if self.macro_worker.is_running:
            self.macro_worker.stop()
            self.macro_worker.wait()
        keyboard.unhook_all()
        save_settings()
        QApplication.quit()

    def start_key_binding(self, key):
        self.waiting_for_key = key
        self.status_label.setText('키를 입력해주세요. 취소하려면 ESC 버튼을 누르세요.')
        set_button_enabled(False)

    @override
    def keyPressEvent(self, event):
        if not self.waiting_for_key:
            return

        key_code = event.key()
        key_text = event.text().upper()
        if not key_text:
            key_text = convert_key_code_to_text(key_code)

        if key_code == Qt.Key_Escape:
            set_button_enabled(True)
            keys[self.waiting_for_key]['key'] = None
            keys[self.waiting_for_key]['label'].setText(f'{keys[self.waiting_for_key]['name']} 키: 미설정')
            self.waiting_for_key = None
            self.status_label.setText('버튼을 눌러 키를 설정하세요.')
            save_settings()
            return

        is_macro_key = self.waiting_for_key == 'macro_key'
        number_pressed = 48 <= key_code <= 57

        if (number_pressed and not is_macro_key) or (is_macro_key and not number_pressed):
            # 키 중복 체크
            for key, value in keys.items():
                if value['key'] == key_text and self.waiting_for_key != key:
                    self.status_label.setText(f'{value['name']}에 이미 설정된 키입니다.')
                    return

            keys[self.waiting_for_key]['key'] = key_text
            keys[self.waiting_for_key]['label'].setText(
                f'{keys[self.waiting_for_key]['name']} 키: {key_text}')
            set_button_enabled(True)

            if is_macro_key:
                self.setup_global_hotkey()
            else:
                self.status_label.setText(f'{keys[self.waiting_for_key]['name']} 키가 설정되었습니다!')

            # 설정 저장
            save_settings()

            # 상태 초기화
            self.waiting_for_key = None
        else:
            self.status_label.setText('숫자만 입력 가능합니다.' if not is_macro_key else '숫자는 입력 불가합니다.')


def convert_key_code_to_text(key_code):
    return key_map.get(key_code, '')


def set_button_enabled(is_enabled):
    """모든 키 설정 버튼의 활성화 상태를 변경"""
    for value in keys.values():
        value['button'].setEnabled(is_enabled)


def main():
    app = QApplication(sys.argv)

    # 시스템 트레이 지원 확인
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print('시스템 트레이를 지원하지 않는 시스템입니다.')
        sys.exit(1)

    # 앱 스타일 설정
    app.setStyle('Fusion')

    # 응용프로그램 아이콘 설정
    if ICON.exists():
        app.setWindowIcon(QIcon(str(ICON)))

    QApplication.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    pydirectinput.PAUSE = 0.01
    pydirectinput.FAILSAFE = False
    main()
