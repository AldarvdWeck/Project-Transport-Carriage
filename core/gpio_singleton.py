# core/gpio_singleton.py
from core.gpio_manager import GPIOManager

# Eén gedeelde GPIOManager voor de hele applicatie
gpio = GPIOManager("config.yaml")