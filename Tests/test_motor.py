#!/usr/bin/env python3
"""
Eenvoudige test voor IBT-2 / motor-aansluiting.

Let op:
- Zorg dat config.yaml de devices bevat:
    motor_rpwm (type: pwm)
    motor_lpwm (type: pwm)
    motor_ren  (type: output)
    motor_len  (type: output)
- Zorg dat:
    RPWM → GPIO18
    LPWM → GPIO19
    R_EN → GPIO23
    L_EN → GPIO24
    GND  → gedeeld tussen Pi, IBT-2 en motorvoeding
"""

from time import sleep
from core.gpio_singleton import gpio


MOTOR_RPWM = "motor_rpwm"
MOTOR_LPWM = "motor_lpwm"
MOTOR_REN = "motor_ren"
MOTOR_LEN = "motor_len"


def all_off():
    """Zet alle motor-signalen uit (coast)."""
    try:
        gpio.set_value(MOTOR_RPWM, 0.0)
    except Exception:
        pass
    try:
        gpio.set_value(MOTOR_LPWM, 0.0)
    except Exception:
        pass
    try:
        gpio.off(MOTOR_REN)
    except Exception:
        pass
    try:
        gpio.off(MOTOR_LEN)
    except Exception:
        pass


def test_forward(speed: float = 0.5, duration: float = 2.0):
    print(f"\n[TEST] Vooruit ({speed*100:.0f}% duty) voor {duration} s")

    # Beide enables aan
    gpio.on(MOTOR_REN)
    gpio.on(MOTOR_LEN)

    # Richting via PWM: rechts aan, links uit
    gpio.set_value(MOTOR_LPWM, 0.0)
    gpio.set_value(MOTOR_RPWM, speed)

    sleep(duration)

    print("[TEST] Stop (coast)")
    all_off()


def test_backward(speed: float = 0.5, duration: float = 2.0):
    print(f"\n[TEST] Achteruit ({speed*100:.0f}% duty) voor {duration} s")

    # Beide enables aan
    gpio.on(MOTOR_REN)
    gpio.on(MOTOR_LEN)

    # Richting via PWM: links aan, rechts uit
    gpio.set_value(MOTOR_RPWM, 0.0)
    gpio.set_value(MOTOR_LPWM, speed)

    sleep(duration)

    print("[TEST] Stop (coast)")
    all_off()



def main():
    print("=== IBT-2 / Motor test ===")
    print("Zorg dat:")
    print("- IBT-2 logica-VCC aan 5V Pi hangt")
    print("- IBT-2 GND aan Pi-GND én motorvoeding-GND hangt")
    print("- Motorvoeding aanwezig is (bijv. 12V)")
    print("- RPWM/LPWM/R_EN/L_EN overeenkomen met config.yaml\n")

    try:
        input("Druk Enter om VOORUIT te testen...")
        test_forward(speed=0.5, duration=2.0)

        input("\nDruk Enter om ACHTERUIT te testen...")
        test_backward(speed=0.5, duration=2.0)

        print("\nKlaar met testen, motor wordt gestopt.")
        all_off()

    except KeyboardInterrupt:
        print("\n[CTRL+C] Onderbroken door gebruiker.")
    finally:
        print("GPIO shutdown...")
        gpio.shutdown()
        print("Einde test.")


if __name__ == "__main__":
    main()
