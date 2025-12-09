from gpio_manager import GPIOManager
from time import sleep
import signal
import sys

gpio = GPIOManager("config.yaml")

def cleanup(sig=None, frame=None):
    gpio.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

gpio.on("status_led")
sleep(1)
gpio.off("status_led")

if gpio.is_pressed("start_button"):
    gpio.on("relay_main")

gpio.set_value("fan", 0.6)

cleanup()
