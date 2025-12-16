# homing routines

from core.gpio_singleton import gpio


def is_home_sensor_xaxis_active() -> bool:
    """
    Lees de homing sensor (inductieve sensor).

    Config:
        sensor_1:
          type: button
          pin: 27
          pull_up: true

    Betekenis:
        - pull_up = True
        - GPIO LOW  -> sensor actief
        - GPIO HIGH -> sensor niet actief
    """

    try:
        value = gpio.read("sensor_1")
    except Exception as e:
        raise RuntimeError(f"Homing sensor uitlezen mislukt: {e}")

    # pull_up=True → actief = LOW
    return not bool(value)
