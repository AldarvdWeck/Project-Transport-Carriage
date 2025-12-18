# hardware/encoder_state.py
import threading
import time

class EncoderState:
    def __init__(self, mm_per_rev: float = 50.0, direction_sign: int = +1):
        self._lock = threading.Lock()

        self.mm_per_rev = float(mm_per_rev)
        self.direction_sign = int(direction_sign)

        self._last_raw = None
        self._turns = 0
        self._home_cont_deg = None

        # Cached output (laatste sample)
        self._latest = {
            "ts": None,
            "raw_deg": None,
            "cont_deg": None,
            "mm": None,
            "delta_deg": None,
        }

    def _cont_deg_from_raw_locked(self, raw_deg: float) -> float:
        raw = float(raw_deg)

        if self._last_raw is None:
            self._last_raw = raw
            return raw

        delta = raw - self._last_raw

        if delta < -180:
            self._turns += 1
        elif delta > 180:
            self._turns -= 1

        self._last_raw = raw
        return self._turns * 360.0 + raw

    # ✅ Deze roep je EXACT 1x per nieuwe Arduino meting aan
    def ingest_raw(self, raw_angle_deg: float, clamp_min_zero: bool = False):
        with self._lock:
            cont = self._cont_deg_from_raw_locked(raw_angle_deg)

            if self._home_cont_deg is None:
                mm = 0.0
                delta_deg = None
            else:
                delta_deg = cont - self._home_cont_deg
                mm = self.direction_sign * (delta_deg * (self.mm_per_rev / 360.0))

            if clamp_min_zero and mm < 0:
                mm = 0.0

            self._latest.update(
                ts=time.time(),
                raw_deg=float(raw_angle_deg),
                cont_deg=float(cont),
                mm=float(mm),
                delta_deg=None if delta_deg is None else float(delta_deg),
            )

    # ✅ Alleen lezen, GEEN unwrap / state changes
    def get_latest(self):
        with self._lock:
            return dict(self._latest)

    def set_home_offset(self, raw_angle_deg: float):
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
        
        # print(f"[EncoderState] raw_angle_deg = {raw_angle_deg}")
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
            
            # print(
            #     f"[EncoderState] cont={cont:.2f}, "
            #     f"home={self._home_cont_deg}, "
            #     f"mm={mm:.3f}"
            # )
                   
            return mm

    # Backwards compatibility: als je ergens nog apply() gebruikt
    def apply(self, raw_angle_deg: float) -> float:
        """Voorheen: homed angle. Nu: return positie in mm."""
        return self.get_position_mm(raw_angle_deg)
