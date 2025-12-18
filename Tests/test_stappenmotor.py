# test_stappenmotor.py
import time
from core.gpio_singleton import gpio


# ---- Config: namen zoals in config.yaml ----
RPWM = "motor_rpwm"
LPWM = "motor_lpwm"
REN  = "motor_ren"
LEN  = "motor_len"

STATUS_LED = "status_led"


def all_stop():
    """Motor veilig uit: PWM=0 en enables uit."""
    try:
        gpio.set_value(RPWM, 0.0)
        gpio.set_value(LPWM, 0.0)
    except Exception:
        pass

    # Enablers uit
    try:
        gpio.off(REN)
        gpio.off(LEN)
    except Exception:
        pass


def enable_driver(enable: bool = True):
    """Zet de enable pins aan/uit."""
    if enable:
        gpio.on(REN)
        gpio.on(LEN)
    else:
        gpio.off(REN)
        gpio.off(LEN)


def set_direction(forward: bool):
    """
    Kies 'richting' door slechts één PWM-kanaal te gebruiken.
    forward=True  -> RPWM actief, LPWM 0
    forward=False -> LPWM actief, RPWM 0
    """
    if forward:
        gpio.set_value(LPWM, 0.0)
    else:
        gpio.set_value(RPWM, 0.0)


def run_motor(forward: bool, duty: float, duration_s: float):
    """
    Laat motor draaien:
      - forward bepaalt welk kanaal actief is
      - duty 0.0..1.0
      - duration in seconden
    """
    duty = max(0.0, min(1.0, duty))

    set_direction(forward)
    if forward:
        gpio.set_value(RPWM, duty)
    else:
        gpio.set_value(LPWM, duty)

    time.sleep(duration_s)


def ramp_test(forward: bool, start: float, end: float, step: float, step_time: float):
    """
    Ramps duty van start naar end in stapjes.
    start/end: 0.0..1.0
    step: bijv 0.05
    step_time: tijd per stap (s)
    """
    if step <= 0:
        raise ValueError("step moet > 0 zijn")

    # Zorg dat de juiste richting “klaarstaat”
    set_direction(forward)

    # Ramp op/af
    if start <= end:
        duty_values = frange(start, end, step)
    else:
        duty_values = frange(start, end, -step)

    for d in duty_values:
        d = max(0.0, min(1.0, d))
        if forward:
            gpio.set_value(RPWM, d)
            gpio.set_value(LPWM, 0.0)
        else:
            gpio.set_value(LPWM, d)
            gpio.set_value(RPWM, 0.0)

        print(f"{'FWD' if forward else 'REV'} duty={d:.2f}")
        time.sleep(step_time)


def frange(start, stop, step):
    """Float-range inclusief eindpunt (ongeveer)."""
    x = start
    if step == 0:
        raise ValueError("step mag niet 0 zijn")

    # Itereer totdat we voorbij stop gaan
    if step > 0:
        while x <= stop + 1e-9:
            yield x
            x += step
    else:
        while x >= stop - 1e-9:
            yield x
            x += step


def main():
    print("=== Motor test gestart ===")
    print("CTRL+C om te stoppen\n")

    # Status LED aan als “we leven”
    try:
        gpio.on(STATUS_LED)
    except Exception:
        pass

    all_stop()
    enable_driver(True)

    try:
        # 1) Korte tik vooruit
        print("1) Korte tik vooruit (duty 0.25, 1s)")
        run_motor(forward=True, duty=0.25, duration_s=1.0)
        all_stop()
        time.sleep(0.5)

        # 2) Ramp vooruit
        print("2) Ramp vooruit 0.20 -> 0.60")
        ramp_test(forward=True, start=0.20, end=0.60, step=0.05, step_time=0.5)
        all_stop()
        time.sleep(0.8)

        # 3) Ramp terug
        print("3) Ramp terug 0.20 -> 0.60")
        ramp_test(forward=False, start=0.20, end=0.60, step=0.05, step_time=0.5)
        all_stop()
        time.sleep(0.8)

        # 4) Langere run vooruit op vaste duty
        print("4) 5 seconden vooruit op duty 0.40")
        run_motor(forward=True, duty=0.40, duration_s=5.0)
        all_stop()

        print("\nKlaar. Motor staat uit.")

    except KeyboardInterrupt:
        print("\nCTRL+C gedetecteerd → motor uit.")
    finally:
        all_stop()
        enable_driver(False)
        try:
            gpio.off(STATUS_LED)
        except Exception:
            pass

        # gpio.close() alleen als je de hele app stopt
        gpio.shutdown()
        print("GPIO shutdown gedaan.")


if __name__ == "__main__":
    main()
