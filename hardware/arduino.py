import time
import serial

class ArduinoController:
    def __init__(self, port='COM6', baud=9600, timeout=0.01):
        self.port, self.baud, self.timeout = port, baud, timeout
        self.ser = None
        self.connected = False
        self.last_reconnect = 0
        self.states = {'RED':False,'BLUE':False,'WHITE':False,'SPEED':0}
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            time.sleep(1.5); self.connected=True; return True
        except Exception:
            self.ser=None; self.connected=False; return False
    def reconnect(self, interval=3):
        if self.connected or time.time()-self.last_reconnect < interval: return self.connected
        self.last_reconnect=time.time(); return self.connect()
    def send(self, command):
        if not self.ser: return False
        try: self.ser.write((command+'\n').encode()); return True
        except Exception: self.connected=False; return False
    def poll(self):
        if not self.ser: return
        try:
            while self.ser.in_waiting:
                line=self.ser.readline().decode(errors='ignore').strip()
                if line.startswith('STATE:'):
                    parts=line.split(':',2)
                    if len(parts)==3:
                        key,val=parts[1],parts[2]
                        self.states[key] = int(val) if key=='SPEED' else val=='ON'
        except Exception: self.connected=False
    def close(self):
        if self.ser:
            try: self.ser.close()
            except Exception: pass
        self.connected=False
