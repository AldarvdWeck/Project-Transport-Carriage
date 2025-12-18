import glob
import threading
import time
import serial


# --- Singleton reader (1x serial verbinding voor hele app) ---
_reader_singleton = None

def get_arduino_reader():
    global _reader_singleton
    if _reader_singleton is None:
        _reader_singleton = ArduinoSensorReader(baudrate=115200)
        _reader_singleton.start()
    return _reader_singleton

class ArduinoSensorReader:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate

        self._lock = threading.Lock()
        self._latest = {
            "angle_deg": None,
            "pot_raw": None,
            "ts": None,
            "port": None,
            "ok": False,
            "last_line": None,
            "error": None,
        }

        self._stop = False
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def get_latest(self):
        with self._lock:
            return dict(self._latest)

    def _find_port(self):
        ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
        return ports[0] if ports else None

    def _run(self):
        while not self._stop:
            port = self._find_port()
            if not port:
                with self._lock:
                    self._latest.update(ok=False, error="No serial port found", port=None)
                time.sleep(1.0)
                continue

            try:
                with self._lock:
                    self._latest.update(port=port, error=None)

                with serial.Serial(port, self.baudrate, timeout=1) as ser:
                    # Uno reset vaak bij openen van serial -> even wachten
                    time.sleep(1.5)

                    while not self._stop:
                        line = ser.readline().decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue
                        
                        # print(f"[ArduinoReader] RX: '{line}'")

                        # verwacht "angle,pot"
                        try:
                            angle_s, pot_s = line.split(",", 1)
                            angle = float(angle_s)
                            pot = int(pot_s)

                            with self._lock:
                                self._latest.update(
                                    angle_deg=angle,
                                    pot_raw=pot,
                                    ts=time.time(),
                                    ok=True,
                                    last_line=line,
                                    error=None,
                                )
                        except Exception:
                            with self._lock:
                                self._latest.update(
                                    ok=False,
                                    last_line=line,
                                    error="Parse error",
                                )

            except Exception as e:
                with self._lock:
                    self._latest.update(ok=False, error=str(e))
                time.sleep(1.0)
