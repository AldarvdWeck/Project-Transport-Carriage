from pathlib import Path
import csv
import time
from typing import Optional

from hardware.encoder import read_encoder_angle_deg
from hardware.motor_controller import TransportMotor
from core.homing import is_home_sensor_xaxis_active

MM_PER_REV = 90.19


def load_station_positions(csv_path: Path | str | None = None) -> dict[int, float]:
    if csv_path is None:
        csv_path = Path(__file__).resolve().parents[1] / "data" / "stations.csv"
    csv_path = Path(csv_path)

    positions: dict[int, float] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row["id"].strip())
            pos = float(row["positie"].strip())
            positions[sid] = pos
    return positions


class EncoderTracker:
    def __init__(self):
        self.last_angle: Optional[float] = None
        self.angle_abs: float = 0.0

    def update_mm(self) -> Optional[float]:
        angle = read_encoder_angle_deg()  # 0..360
        if angle is None:
            return None

        if self.last_angle is None:
            self.last_angle = angle
            return (self.angle_abs / 360.0) * MM_PER_REV

        d = angle - self.last_angle

        if d > 180:
            d -= 360
        elif d < -180:
            d += 360

        self.angle_abs += d
        self.last_angle = angle

        return (self.angle_abs / 360.0) * MM_PER_REV

    def reset_zero(self):
        self.last_angle = None
        self.angle_abs = 0.0


class LinearAxisController:
    def __init__(
        self,
        motor: TransportMotor | None = None,
        encoder: EncoderTracker | None = None,
        home_sensor=is_home_sensor_xaxis_active,
    ):
        self.motor = motor or TransportMotor()
        self.encoder = encoder or EncoderTracker()
        self.home_sensor = home_sensor

    # -----------------------------
    # Basis functies
    # -----------------------------

    def current_position_mm(self) -> Optional[float]:
        return self.encoder.update_mm()

    # -----------------------------
    # Homing
    # -----------------------------

    def home(
        self,
        fast_speed: float = 0.6,
        slow_speed: float = 0.2,
        timeout_s: float = 20.0,
    ) -> bool:

        start = time.monotonic()

        # FASE 1: zoek homing sensor (snel)
        self.motor.backward(fast_speed)
        while not self.home_sensor():
            if time.monotonic() - start > timeout_s:
                self.motor.stop(brake=True)
                return False
            time.sleep(0.01)

        self.motor.stop(brake=True)
        time.sleep(0.2)

        # FASE 2: loskomen
        self.encoder.reset_zero()
        self.motor.forward(slow_speed)

        while self.home_sensor():
            time.sleep(0.01)

        self.motor.stop(brake=True)
        time.sleep(0.2)

        # FASE 3: langzaam opnieuw raken
        self.motor.backward(slow_speed)
        while not self.home_sensor():
            time.sleep(0.01)

        self.motor.stop(brake=True)

        # Definitieve nulpositie
        self.encoder.reset_zero()
        return True

    # -----------------------------
    # Positioneren
    # -----------------------------

    def goto_position_mm(
        self,
        target_mm: float,
        speed: float = 0.6,
        tolerance_mm: float = 2.0,
        slow_zone_mm: float = 10.0,
        timeout_s: float = 30.0,
    ) -> bool:

        start = time.monotonic()

        pos = self.current_position_mm()
        if pos is None:
            raise RuntimeError("Encoder niet beschikbaar bij start")

        while True:
            pos = self.current_position_mm()
            if pos is None:
                time.sleep(0.05)
                continue

            error = target_mm - pos

            if abs(error) <= tolerance_mm:
                self.motor.stop(brake=False)
                return True

            # Snelheid afbouwen dichtbij doel
            cmd_speed = speed
            if abs(error) < slow_zone_mm:
                cmd_speed = min(speed, 0.25)

            if error > 0:
                self.motor.forward(cmd_speed)
            else:
                self.motor.backward(cmd_speed)

            if time.monotonic() - start > timeout_s:
                self.motor.stop(brake=True)
                return False

            time.sleep(0.05)

    # -----------------------------
    # Stations
    # -----------------------------

    def move_between_station_ids(
        self,
        pickup_id: int,
        dropoff_id: int,
        speed: float = 0.6,
    ) -> None:

        positions = load_station_positions()

        if pickup_id not in positions:
            raise KeyError(f"Pickup station {pickup_id} niet gevonden")
        if dropoff_id not in positions:
            raise KeyError(f"Dropoff station {dropoff_id} niet gevonden")

        p_from = positions[pickup_id]
        p_to = positions[dropoff_id]

        if not self.goto_position_mm(p_from, speed=speed):
            raise RuntimeError("Timeout bij rijden naar pickup")

        time.sleep(0.5)

        if not self.goto_position_mm(p_to, speed=speed):
            raise RuntimeError("Timeout bij rijden naar dropoff")
