# hardware/homing2.py
import time
import threading

class HomingController:
    def __init__(self, motor, gpio, arduino_reader, encoder_state,
                 sensor_name="sensor_1",
                 direction="backward",
                 speed=0.4,
                 timeout_s=10.0,
                 settle_s=0.15):
        self.motor = motor
        self.gpio = gpio
        self.reader = arduino_reader
        self.encoder_state = encoder_state

        self.sensor_name = sensor_name
        self.direction = direction
        self.speed = speed
        self.timeout_s = timeout_s
        self.settle_s = settle_s

        self._lock = threading.Lock()
        self._running = False
        self._last_result = None

        self._cancel_event = threading.Event()

    def status(self):
        with self._lock:
            return {
                "running": self._running,
                "last_result": self._last_result
            }

    def start(self):
        self._cancel_event.clear()
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._last_result = None

        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        return True

    def cancel(self):
        with self._lock:
            if not self._running:
                return False
            self._cancel_event.set()
            return True

    def _run(self):
        result = {"success": False, "error": None}

        try:
            # Start bewegen
            if self.direction == "backward":
                self.motor.backward(self.speed)
            else:
                self.motor.forward(self.speed)

            start_t = time.time()

            # Wacht tot sensor triggert, cancel, of timeout
            while True:
                if self._cancel_event.is_set():
                    raise RuntimeError("Homing cancelled by user")

                if self.gpio.is_active(self.sensor_name):
                    break

                if (time.time() - start_t) > self.timeout_s:
                    raise TimeoutError(f"Homing timeout after {self.timeout_s}s")

                time.sleep(0.01)

            # Stop motor
            self.motor.stop(brake=False)

            # Even stabiliseren / bounce vermijden
            time.sleep(self.settle_s)

            # Lees huidige raw encoderwaarde en zet home
            data = self.reader.get_latest()
            if not data.get("ok") or data.get("angle_deg") is None:
                raise RuntimeError(data.get("error", "No encoder data during homing"))

            raw_angle = float(data["angle_deg"])
            self.encoder_state.set_home_offset(raw_angle)

            result["success"] = True
            result["home_offset"] = raw_angle

        except Exception as e:
            try:
                self.motor.stop(brake=False)
            except Exception:
                pass
            result["error"] = str(e)
            result["cancelled"] = self._cancel_event.is_set()

        finally:
            with self._lock:
                self._running = False
                self._last_result = result
