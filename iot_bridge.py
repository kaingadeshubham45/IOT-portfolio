import serial
import serial.tools.list_ports
import time

class IoTBridge:
    def __init__(self, baudrate=9600):
        self.ser = None
        self.baudrate = baudrate
        self.connect()

    def connect(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            try:
                self.ser = serial.Serial(p.device, self.baudrate, timeout=0.1)
                time.sleep(1)
                print(f"[IoT Bridge] Connected to hardware on {p.device}")
                return
            except Exception:
                continue
        print("[IoT Bridge] Running in Emulation Mode (No Serial Port Detected)")

    def send(self, command: str):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{command}\n".encode('utf-8'))
            except Exception:
                pass
        else:
            pass

iot = IoTBridge()
