import os
import subprocess
import time
from core.gpio_singleton import gpio
from time import sleep
import signal
import sys
from HMI.app import app
from threading import Thread

def start_flask():
    print("Transport HMI Server wordt gestart op http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)

flask_thread = Thread(target=start_flask, daemon=True)
flask_thread.start()

def cleanup(sig=None, frame=None):
    print("Shutting down…")
    gpio.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ---- Browser openen ----
time.sleep(2)  # wachten tot Flask server draait

# Forceer DISPLAY naar de desktop sessie
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"   # typische display van de eerste GUI sessie

try:
    print(f"DISPLAY = {os.environ.get('DISPLAY')}, probeer Chromium te starten...")
    subprocess.Popen([
        "chromium",
        "--kiosk",
        "--disable-infobars",
        "--noerrdialogs",
        "--incognito",
        "--log-level=3",      # minder Chromium spam
        "http://localhost:5000"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception as e:
    print("Kon Chromium niet starten:", e)


print("HMI gestart in fullscreen. Druk Ctrl+C om te stoppen.")

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    cleanup()
