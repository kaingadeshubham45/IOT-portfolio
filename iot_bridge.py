import serial

class IoTBridge:
    def __init__(self, port="COM3", baud=9600):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            print(f"[IoT Bridge] Connected to hardware on {port}")
        except Exception:
            print("[IoT Bridge] Running in Simulation Mode (No hardware connected)")

    def send(self, command: str):
        if self.ser and self.ser.is_open:
            self.ser.write(f"{command}\n".encode())
        print(f"[IoT Outbound Signal]: {command}")

iot = IoTBridge()