# hardware/encoder_state.py
import threading

class EncoderState:
    """
    - raw_angle_deg komt van Arduino (AS5600) in bereik 0..360
    - we unwrappen dit naar continue graden (kan >360 of <0 worden)
    - homing: slaat de continue hoek op als nul-referentie
    - output: positie in mm t.o.v. home
    """

    def __init__(self, mm_per_rev: float = 50.0, direction_sign: int = +1):
        self._lock = threading.Lock()

        # Calibratie / tuning
        self.mm_per_rev = float(mm_per_rev)     # later aanpassen
        self.direction_sign = int(direction_sign)  # +1 of -1

        # Unwrap state
        self._last_raw = None   # laatste raw 0..360
        self._turns = 0         # aantal volledige omwentelingen (+/-)

        # Home state
        self._home_cont_deg = None  # continue graden op home-moment

    # ---------- Unwrap helpers ----------
    def _cont_deg_from_raw_locked(self, raw_deg: float) -> float:
        raw = float(raw_deg)

        if self._last_raw is None:
            self._last_raw = raw
            return raw

        delta = raw - self._last_raw

        # wrap detectie
        # 359 -> 0  => delta ~ -359  -> we gingen vooruit => turns +1
        # 0 -> 359  => delta ~ +359  -> we gingen achteruit => turns -1
        if delta < -180:
            self._turns += 1
        elif delta > 180:
            self._turns -= 1

        self._last_raw = raw
        return self._turns * 360.0 + raw

    def update_raw(self, raw_deg: float) -> float:
        """Optioneel: roep aan als je alleen state wilt bijwerken."""
        with self._lock:
            return self._cont_deg_from_raw_locked(raw_deg)

    # ---------- Homing ----------
    def set_home_offset(self, raw_angle_deg: float):
        """
        Hou dezelfde functienaam aan zodat je homing2.py minimaal hoeft te wijzigen.
        Maar intern slaan we nu de continue hoek op als 'home'.
        """
        with self._lock:
            cont = self._cont_deg_from_raw_locked(raw_angle_deg)
            self._home_cont_deg = cont

    def clear_home(self):
        with self._lock:
            self._home_cont_deg = None

    def is_homed(self) -> bool:
        with self._lock:
            return self._home_cont_deg is not None

    # ---------- Output ----------
    def get_position_mm(self, raw_angle_deg: float, clamp_min_zero: bool = False) -> float:
        """
        Geef positie in mm terug t.o.v. home.
        clamp_min_zero=True maakt negatieve waarden 0 (handig als home aan eindstop zit).
        """
        with self._lock:
            cont = self._cont_deg_from_raw_locked(raw_angle_deg)

            if self._home_cont_deg is None:
                mm = 0.0
            else:
                delta_deg = cont - self._home_cont_deg
                mm_per_deg = self.mm_per_rev / 360.0
                mm = self.direction_sign * (delta_deg * mm_per_deg)

            if clamp_min_zero and mm < 0:
                mm = 0.0

            return mm

    # Backwards compatibility: als je ergens nog apply() gebruikt
    def apply(self, raw_angle_deg: float) -> float:
        """Voorheen: homed angle. Nu: return positie in mm."""
        return self.get_position_mm(raw_angle_deg)
