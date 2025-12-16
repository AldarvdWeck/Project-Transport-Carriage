from core.gpio_singleton import gpio


class TransportMotor:
    """
    Wrapper om een IBT-2 (BTS7960) H-brug te sturen via jullie GPIOManager.
    Verwacht in config.yaml:
      motor_rpwm (pwm)
      motor_lpwm (pwm)
      motor_ren  (output)
      motor_len  (output)
    """

    def __init__(self,
                 rpwm_name: str = "motor_rpwm",
                 lpwm_name: str = "motor_lpwm",
                 ren_name: str = "motor_ren",
                 len_name: str = "motor_len") -> None:
        self.rpwm_name = rpwm_name
        self.lpwm_name = lpwm_name
        self.ren_name = ren_name
        self.len_name = len_name

    @staticmethod
    def _clamp_speed(speed: float) -> float:
        """Beperk snelheid tot [0.0, 1.0]."""
        return max(0.0, min(1.0, float(speed)))

    def forward(self, speed: float = 1.0) -> None:
        """
        Laat de motor vooruit draaien.
        BTS7960: Beide EN-pinnen aan, richting via RPWM/LPWM.
        speed: 0.0 t/m 1.0 (duty cycle)
        """
        speed = self._clamp_speed(speed)

        # *** BEIDE enables AAN ***
        gpio.on(self.ren_name)
        gpio.on(self.len_name)

        # Richting bepalen: vooruit = RPWM PWM, LPWM 0
        gpio.set_value(self.lpwm_name, 0.0)
        gpio.set_value(self.rpwm_name, speed)

    def backward(self, speed: float = 1.0) -> None:
        """
        Laat de motor achteruit draaien.
        BTS7960: Beide EN-pinnen aan, richting via RPWM/LPWM.
        speed: 0.0 t/m 1.0 (duty cycle)
        """
        speed = self._clamp_speed(speed)

        # *** BEIDE enables AAN ***
        gpio.on(self.ren_name)
        gpio.on(self.len_name)

        # Richting bepalen: achteruit = LPWM PWM, RPWM 0
        gpio.set_value(self.rpwm_name, 0.0)
        gpio.set_value(self.lpwm_name, speed)

    def coast(self) -> None:
        """
        Motor laten 'uitrollen':
        beide enables UIT → H-brug in high-impedance (coast).
        """
        gpio.off(self.ren_name)
        gpio.off(self.len_name)
        gpio.set_value(self.rpwm_name, 0.0)
        gpio.set_value(self.lpwm_name, 0.0)

    def brake(self) -> None:
        """
        Actief remmen:
        beide enables AAN maar geen PWM → beide half-bridges actief.
        (IBT-2 remt hierdoor sterk)
        """
        gpio.on(self.ren_name)
        gpio.on(self.len_name)
        gpio.set_value(self.rpwm_name, 0.0)
        gpio.set_value(self.lpwm_name, 0.0)

    def stop(self, brake: bool = False) -> None:
        """
        Stop de motor: coast (standaard) of remmen via brake().
        """
        if brake:
            self.brake()
        else:
            self.coast()
