# main.py (Kivy 앱 메인 코드)
from jnius import autoclass
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
# Android Bluetooth API 클래스 로드
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
UUID = autoclass('java.util.UUID')

# 블루투스 소켓 초기화 함수
def init_bt_socket(device_name="HC-05"):
    adapter = BluetoothAdapter.getDefaultAdapter()
    paired_devices = adapter.getBondedDevices().toArray()  # 페어링된 장치 목록
    for device in paired_devices:
        if device.getName() == device_name:               # 이름으로 HC-05 찾기
            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")  # SPP UUID
            socket = device.createRfcommSocketToServiceRecord(uuid)
            socket.connect()                              # HC-05 RFCOMM 소켓 연결:contentReference[oaicite:3]{index=3}
            return socket
    return None

class DualStickApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bt_socket = None
        self.bt_out = None
        # 현재 조이스틱 입력값 저장 (튜플 형태)
        self.left_pad = (0.0, 0.0)
        self.right_pad = (0.0, 0.0)

    def build(self):
        # Bluetooth 권한 요청 (Android 12 이상 필요)
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.BLUETOOTH_CONNECT, Permission.BLUETOOTH_SCAN])
        except ImportError:
            pass  # 안드로이드 환경이 아닐 경우 패스

        # 블루투스 소켓 연결
        socket = init_bt_socket("HC-05")
        if socket:
            self.bt_socket = socket
            self.bt_out = socket.getOutputStream()  # 출력 스트림 얻기

        # .kv 파일 레이아웃 불러오기
        return BoxLayout()  # 실제 레이아웃은 .kv에서 정의

    def on_pad(self, stick, pad):  # 조이스틱 이동 콜백 (stick: 'left'/'right')
        # pad: (x,y), 각 -1.0 ~ 1.0 범위 (0,0은 중립)
        if stick == 'left':
            self.left_pad = pad
        else:
            self.right_pad = pad
        # 두 스틱 값 모두 활용하여 명령 문자열 생성
        lx, ly = self.left_pad  # 좌측 스틱 (lx: 좌우, ly: 상하)
        rx, ry = self.right_pad  # 우측 스틱 (rx: 좌우, ry: 상하)
        # -1.0~1.0 범위를 -100~100 정수로 변환
        cmd = "{},{},{},{}".format(int(lx*100), int(ly*100), int(rx*100), int(ry*100))
        # 블루투스으로 전송
        if self.bt_out:
            self.bt_out.write((cmd + "\n").encode('utf-8'))  # 줄바꿈 기준 한 패킷
            self.bt_out.flush()

if __name__ == "__main__":
    DualStickApp().run()
