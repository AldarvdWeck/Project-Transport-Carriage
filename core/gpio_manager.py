import yaml
from gpiozero import LED, Button, OutputDevice, PWMOutputDevice


class GPIOManager:
    def __init__(self, config_path="config.yaml"):
        self.devices = {}
        self.config = self._load_config(config_path)
        self._validate_config()
        self._init_devices()

    # ---------- CONFIG ----------
    def _load_config(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)["gpio"]

    def _validate_config(self):
        used_pins = set()
        valid_types = {"led", "output", "pwm", "button"}

        for name, cfg in self.config.items():
            pin = cfg["pin"]
            t = cfg["type"]

            if pin in used_pins:
                raise ValueError(f"GPIO {pin} wordt dubbel gebruikt")

            if t not in valid_types:
                raise ValueError(f"Onbekend type '{t}' bij {name}")

            used_pins.add(pin)

    # ---------- INIT ----------
    def _init_devices(self):
        for name, cfg in self.config.items():
            t = cfg["type"]
            pin = cfg["pin"]

            if t == "led":
                self.devices[name] = LED(pin, initial_value=False)

            elif t == "output":
                self.devices[name] = OutputDevice(
                    pin,
                    active_high=cfg.get("active_high", True),
                    initial_value=False
                )

            elif t == "pwm":
                self.devices[name] = PWMOutputDevice(
                    pin,
                    frequency=cfg.get("frequency", 1000)
                )

            elif t == "button":
                self.devices[name] = Button(
                    pin,
                    pull_up=cfg.get("pull_up", True)
                )

    # ---------- API ----------
    def on(self, name):
        self.devices[name].on()

    def off(self, name):
        self.devices[name].off()

    def set_value(self, name, value):
        self.devices[name].value = value

    def is_pressed(self, name):
        return self.devices[name].is_pressed

    def is_active(self, name):
        return bool(self.devices[name].is_active)

    # ---------- SHUTDOWN ----------
    def shutdown(self):
        for dev in self.devices.values():
            dev.close()
