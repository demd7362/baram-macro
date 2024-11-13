import os
import sys
import time
from pathlib import Path

import cv2
import keyboard
import numpy
import pyautogui
import pydirectinput
from PyQt5.QtCore import Qt, QSize, QUrl, QThread
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QSystemTrayIcon, QMenu, QStyle, QHBoxLayout, QFrame, QCheckBox
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

monsters = set()

ghost_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'ghost.png'), 0)
chogeup_ghost_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'chogeup_ghost.png'), 0)
gogeup_ghost_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'gogeup_ghost.png'), 0)
jeongal_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'jeongal.png'), 0)
jeongaljang_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'jeongaljang.png'), 0)
seohyeon_gajae_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'seohyeon_gajae.png'), 0)
templates = {
    "전갈": jeongal_template,
    "전갈장": jeongaljang_template,
    "서현가재": seohyeon_gajae_template,
    "유령": ghost_template,
    "초급유령": chogeup_ghost_template,
    "고급유령": gogeup_ghost_template
}

quit_button_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'quit_button.png'), 0)
disabled_ok_button_template = cv2.imread(
    os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'disabled_ok_button.png'), 0)
king_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'king.png'), 0)
cancel_template = cv2.imread(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'cancel.png'), 0)

MACRO_NAME = '왕퀘 헬퍼'
ICON = Path(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), 'assets', 'king.png'))
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
    print(f'max val{max_val}')
    return max_val >= 0.99


def find_and_click_template(template, confidence=0.9):
    screen_gray = capture_screen()
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        # 템플릿 이미지의 중심점 계산
        template_height, template_width = template.shape
        center_x = max_loc[0] + template_width // 2
        center_y = max_loc[1] + template_height // 2

        pyautogui.click(center_x, center_y)
        return True

    return False


class MacroWorker(QThread):
    def __init__(self):
        super().__init__()
        self.is_running = False

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            clicked = find_and_click_template(king_template)
            time.sleep(0.5)
            if not clicked:
                pydirectinput.press('esc')
                continue
            screen_gray = capture_screen()
            ui_open = analyze_screen(screen_gray, quit_button_template)
            if not ui_open:
                continue

            is_cancel = analyze_screen(screen_gray, cancel_template)
            if is_cancel:
                print('왕퀘 취소 메세지')
                time.sleep(0.5)
                pydirectinput.press('enter')
                time.sleep(0.5)
                pydirectinput.press('enter')
                time.sleep(0.5)
                pydirectinput.press('down')
                time.sleep(0.5)
                pydirectinput.press('enter')
                time.sleep(0.5)
                pydirectinput.press('enter')
                continue
            print('왕퀘 시작 메세지')
            pydirectinput.press('enter')
            time.sleep(0.5)
            pydirectinput.press('enter')
            time.sleep(0.5)
            pydirectinput.press('down')
            time.sleep(0.5)
            pydirectinput.press('enter')
            time.sleep(0.5)
            screen_gray = capture_screen()
            for monster in monsters:
                found = analyze_screen(screen_gray, templates[monster])
                if found:
                    print('found')
                    self.is_running = False
                    break
            # pydirectinput.press('enter')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.init_ui()
        self.init_tray()
        self.macro_worker = MacroWorker()
        self.setup_global_hotkey()

    def init_ui(self):
        self.setWindowTitle(MACRO_NAME)
        self.setFixedSize(550, 250)
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
        title_label = QLabel('F7키로 실행/중지 권장 해상도 1920*1080\n찾은 후엔 다시 F7 눌러주세요. 마우스 커서는 치워주세요.')
        title_label.setStyleSheet(StyleSheet.TITLE_LABEL)
        title_layout.addWidget(title_label)
        header_layout.addLayout(title_layout)

        github_button = QPushButton()
        github_button.setStyleSheet(StyleSheet.GITHUB_BUTTON)
        github_button.setToolTip("GitHub 저장소 방문")
        github_button.setIcon(QIcon(str(GITHUB_ICON)))
        github_button.setIconSize(QSize(28, 28))
        github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/demd7362/baram-helper")))
        header_layout.addWidget(github_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addWidget(header_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e9ecef;")
        main_layout.addWidget(separator)

        self.status_label = QLabel('F7 키로 실행')
        self.status_label.setStyleSheet(StyleSheet.STATUS_LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

        checkbox_layout = QHBoxLayout()
        self.checkboxes = {
            "전갈": QCheckBox("전갈"),
            "전갈장": QCheckBox("전갈장"),
            "서현가재": QCheckBox("서현가재"),
            "유령": QCheckBox("유령"),
            "초급유령": QCheckBox("초급유령"),
            "고급유령": QCheckBox("고급유령")
        }
        for checkbox in self.checkboxes.values():
            checkbox.stateChanged.connect(self.update_monsters)
            checkbox_layout.addWidget(checkbox)
        main_layout.addLayout(checkbox_layout)

    def update_monsters(self, state):
        checkbox = self.sender()
        monster = next(k for k, v in self.checkboxes.items() if v == checkbox)
        if state == Qt.Checked:
            monsters.add(monster)
        else:
            monsters.discard(monster)

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
        keyboard.on_press_key('f7', lambda _: self.toggle_macro())

    def toggle_macro(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.macro_worker.is_running = True
            self.macro_worker.start()
            self.status_label.setText('실행중...')
            self.tray_icon.showMessage(MACRO_NAME, "매크로 실행", QSystemTrayIcon.Information, 2000)
        else:
            self.macro_worker.stop()
            self.status_label.setText('중지되었습니다.')
            self.tray_icon.showMessage(MACRO_NAME, "매크로 중지", QSystemTrayIcon.Information, 2000)

    def press_and_enter(self):
        time.sleep(0.03)  # 약간의 딜레이
        pydirectinput.press('enter')

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
        QApplication.quit()


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
