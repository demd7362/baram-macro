import sys
import time

import keyboard
import pydirectinput
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QSystemTrayIcon, QMenu)

macro_name = '도사 매크로'
keys = {
    'macro_key': {
        'name': '매크로 실행',
        'label': None,
        'key': None,
        'button': None
    },
    'giwon': {
        'name': '기원',
        'label': None,
        'key': None,
        'button': None
    },
    'honma': {
        'name': '혼마술',
        'label': None,
        'key': None,
        'button': None
    },
    'gongjeung': {
        'name': '공력증강',
        'label': None,
        'key': None,
        'button': None
    },
    'geumgang': {
        'name': '금강불체',
        'label': None,
        'key': None,
        'button': None
    }
}


class MacroWorker(QThread):
    """매크로 동작을 위한 워커 스레드"""

    def __init__(self):
        super().__init__()
        self.is_running = False

    def run(self):
        while self.is_running:
            try:
                honma_key = keys['honma']['key']
                pydirectinput.keyDown(honma_key)
                pydirectinput.keyUp(honma_key)
                pydirectinput.keyDown('up')
                pydirectinput.keyUp('up')
                pydirectinput.keyDown('enter')
                pydirectinput.keyUp('enter')
                # 최소한의 딜레이 추가
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in macro: {e}")
                self.is_running = False
                break

    def stop(self):
        self.is_running = False


def convert_key_code_to_text(key_code, key_text=None):
    """
    Qt 키 코드를 pydirectinput 호환 텍스트로 변환

    Args:
        key_code (int): Qt 키 이벤트의 key code
        key_text (str, optional): 기본 키 텍스트. 기본값은 None

    Returns:
        str: pydirectinput 호환 키 텍스트
    """

    # Function keys (F1-F12)
    if key_code == 16777264:
        return 'f1'
    elif key_code == 16777265:
        return 'f2'
    elif key_code == 16777266:
        return 'f3'
    elif key_code == 16777267:
        return 'f4'
    elif key_code == 16777268:
        return 'f5'
    elif key_code == 16777269:
        return 'f6'
    elif key_code == 16777270:
        return 'f7'
    elif key_code == 16777271:
        return 'f8'
    elif key_code == 16777272:
        return 'f9'
    elif key_code == 16777273:
        return 'f10'
    elif key_code == 16777274:
        return 'f11'
    elif key_code == 16777275:
        return 'f12'

    # Special keys
    elif key_code == 16777216:
        return 'esc'
    elif key_code == 16777217:
        return 'tab'
    elif key_code == 16777220:  # 일반 Enter
        return 'enter'
    elif key_code == 16777221:  # 숫자패드 Enter
        return 'enter'
    elif key_code == 16777223:
        return 'backspace'
    elif key_code == 16777219:
        return 'del'
    elif key_code == 16777234:
        return 'left'
    elif key_code == 16777236:
        return 'right'
    elif key_code == 16777235:
        return 'up'
    elif key_code == 16777237:
        return 'down'
    elif key_code == 16777232:
        return 'home'
    elif key_code == 16777233:
        return 'end'
    elif key_code == 16777238:
        return 'pageup'
    elif key_code == 16777239:
        return 'pagedown'
    elif key_code == 16777222:
        return 'insert'
    elif key_code == 16777252:
        return 'capslock'
    elif key_code == 16777248:
        return 'shift'
    elif key_code == 16777249:
        return 'ctrl'
    elif key_code == 16777251:
        return 'alt'
    elif key_code == 32:
        return 'space'

    # 일반 키의 경우 입력된 텍스트를 소문자로 반환
    elif key_text:
        return key_text.lower()

    # 매칭되는 키가 없는 경우
    return ''


def set_button_enabled(is_enabled):
    for value in keys.values():
        value['button'].setEnabled(is_enabled)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.waiting_for_key = None
        self.macro_worker = MacroWorker()
        self.init_ui()
        self.init_tray()
        self.hotkey_listener = None

    def init_ui(self):
        # 창 설정
        self.setWindowTitle(macro_name)
        self.setGeometry(300, 300, 300, 300)

        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 키 위젯 생성
        for [key, value] in keys.items():
            value['button'] = QPushButton(f'{value['name']} 키 설정', self)
            value['button'].clicked.connect(lambda checked, k=key: self.start_key_binding(k))
            layout.addWidget(value['button'])
            value['label'] = QLabel(f'{value['name']} 키: 미설정', self)
            layout.addWidget(value['label'])

        # 상태 표시 라벨
        self.status_label = QLabel('버튼을 눌러 키를 설정하세요.', self)
        layout.addWidget(self.status_label)

        # 실행 상태 표시 라벨
        self.execution_label = QLabel('', self)
        layout.addWidget(self.execution_label)

        self.show()

    def init_tray(self):
        # 시스템 트레이 아이콘 생성
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().SP_ComputerIcon))

        # 트레이 메뉴 생성
        tray_menu = QMenu()
        show_action = tray_menu.addAction("보이기")
        quit_action = tray_menu.addAction("종료")

        # 메뉴 액션 연결
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 트레이 아이콘 더블클릭시 창 보이기
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def setup_global_hotkey(self):
        if self.hotkey_listener:
            keyboard.unhook_all()

        macro_key = keys['macro_key']['key']
        if macro_key:
            keyboard.on_press_key(macro_key.lower(), lambda _: self.toggle_macro())
            self.status_label.setText(f'매크로 실행 키가 {macro_key}로 설정되었습니다.')

    def toggle_macro(self):
        # 바인딩 안된 키 있는지 확인
        for key, value in keys.items():
            if key != 'macro_key' and value['key'] is None:  # 매크로 키는 제외
                self.status_label.setText(f'{value['name']} 키가 등록되지 않았습니다.')
                return

        self.is_running = not self.is_running
        if self.is_running:
            self.status_label.setText('매크로 실행중...')
            set_button_enabled(False)
            self.macro_worker.is_running = True
            self.macro_worker.start()
            self.tray_icon.showMessage(
                macro_name,
                "매크로 실행",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.status_label.setText('매크로가 중지되었습니다.')
            set_button_enabled(True)
            self.macro_worker.stop()
            self.tray_icon.showMessage(
                macro_name,
                "매크로 중지",
                QSystemTrayIcon.Information,
                2000
            )

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                macro_name,
                "프로그램이 시스템 트레이로 최소화되었습니다.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()

    def quit_application(self):
        # 매크로 중지
        if self.macro_worker.is_running:
            self.macro_worker.stop()
            self.macro_worker.wait()
        keyboard.unhook_all()  # 모든 핫키 제거
        QApplication.quit()

    def start_key_binding(self, key):
        self.waiting_for_key = key
        self.status_label.setText('키를 입력해주세요. 취소하려면 esc 버튼을 누르세요.')
        set_button_enabled(False)

    def keyPressEvent(self, event):
        key_code = event.key()
        key_text = event.text().upper()
        if not key_text:
            key_text = convert_key_code_to_text(key_code)
        if key_code == Qt.Key_Escape:  # esc
            set_button_enabled(True)
            keys[self.waiting_for_key]['key'] = None
            keys[self.waiting_for_key]['label'].setText(f'{keys[self.waiting_for_key]['name']} 키: 미설정')
            self.waiting_for_key = None
            self.status_label.setText('버튼을 눌러 키를 설정하세요.')
            return

        is_macro_key = self.waiting_for_key == 'macro_key'
        if self.waiting_for_key:  # 버튼 눌렀을 때
            # 0 ~ 9
            if (48 <= key_code <= 57 and not is_macro_key) or (is_macro_key and not 48 <= key_code <= 57):
                for [key, value] in keys.items(): # check keys
                    # 키가 겹치는게 존재 && 자기 자신의 키가 아님
                    if value['key'] == key_text and self.waiting_for_key != key:
                        self.status_label.setText(f'{value['name']}에 이미 설정된 키입니다.')
                        return

                keys[self.waiting_for_key]['key'] = key_text
                keys[self.waiting_for_key]['label'].setText(
                    f'{keys[self.waiting_for_key]['name']} 키: {key_text}')
                # 모든 버튼 다시 활성화
                set_button_enabled(True)

                if is_macro_key:
                    self.setup_global_hotkey()
                else:
                    self.status_label.setText(f'{keys[self.waiting_for_key]['name']} 키가 설정되었습니다!')

                # 상태 초기화
                self.waiting_for_key = None
            else:  # 숫자가 아니라면
                self.status_label.setText('숫자만 입력 가능합니다.' if not is_macro_key else '숫자는 입력 불가합니다.')


def main():
    app = QApplication(sys.argv)
    # 시스템 트레이 지원 확인
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print('시스템 트레이를 지원하지 않는 시스템입니다.')
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    pydirectinput.PAUSE = 0.01  # 기본 지연 시간 설정
    pydirectinput.FAILSAFE = False  # 안전장치 비활성화
    main()
