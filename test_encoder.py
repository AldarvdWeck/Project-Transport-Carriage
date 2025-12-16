#!/usr/bin/env python3
import time

# Probeer smbus2, anders smbus
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# ---------- AS5600 instellingen ----------
AS5600_ADDR = 0x36
AS5600_RAW_ANGLE = 0x0C  # RAW_ANGLE register (MSB)

# >>>>>> LINEAIRE POSITIE CONFIG <<<<<<
# Zelfde als in jullie Arduino code
MM_PER_REV = 90.19  # mm per volledige omwenteling


class AS5600:
    def __init__(self, bus_num=1, addr=AS5600_ADDR):
        self.bus = SMBus(bus_num)
        self.addr = addr

        # Kalibratie-offset (in raw counts)
        self.zero_offset_raw = None

        # Hoeksnelheid variabelen (gekalibreerde hoek)
        self.last_angle_deg_cal = 0.0
        self.last_time = time.monotonic()

        # Absolute (doortellende) hoek
        self.angle_deg_abs = 0.0

    def read_raw_angle(self):
        """
        Leest de 12-bit RAW_ANGLE waarde (0..4095) uit de AS5600.
        Retourneert None bij I2C-fout.
        """
        try:
            # Direct 2 bytes uit RAW_ANGLE register lezen
            data = self.bus.read_i2c_block_data(self.addr, AS5600_RAW_ANGLE, 2)
        except OSError as e:
            print(f"I2C error: {e}")
            return None

        high = data[0]
        low = data[1]
        raw = ((high << 8) | low) & 0x0FFF  # 12 bits
        return raw

    def update(self):
        """
        Roept deze elke loop aan.
        - Werkt alle waardes bij
        - Geeft dict terug met de huidige waarden
          of None bij een leesfout.
        """
        now = time.monotonic()
        angle_raw = self.read_raw_angle()
        if angle_raw is None:
            return None

        # Eerste meting als nulpositie gebruiken
        if self.zero_offset_raw is None:
            self.zero_offset_raw = angle_raw
            self.last_angle_deg_cal = 0.0
            self.angle_deg_abs = 0.0
            self.last_time = now

        # Gekalibreerde hoek 0..360 t.o.v. zero_offset_raw
        diff_raw = angle_raw - self.zero_offset_raw
        if diff_raw < 0:
            diff_raw += 4096
        angle_deg_cal = (diff_raw * 360.0) / 4096.0

        # Hoeksnelheid + absolute hoek berekenen
        dt = now - self.last_time
        if dt <= 0:
            dt = 1e-3

        d_angle = angle_deg_cal - self.last_angle_deg_cal

        # Wrap-around correctie rond 0/360
        if d_angle > 180:
            d_angle -= 360
        if d_angle < -180:
            d_angle += 360

        # Absolute hoek doortellen
        self.angle_deg_abs += d_angle
        angular_velocity = d_angle / dt

        self.last_angle_deg_cal = angle_deg_cal
        self.last_time = now

        # Positie in mm uit absolute hoek
        position_mm = (self.angle_deg_abs / 360.0) * MM_PER_REV

        return {
            "angle_raw": angle_raw,
            "angle_deg_cal": angle_deg_cal,
            "angle_deg_abs": self.angle_deg_abs,
            "position_mm": position_mm,
            "angular_velocity_dps": angular_velocity,
        }

    def close(self):
        self.bus.close()


def main():
    sensor = AS5600(bus_num=1)
    print(f"AS5600 reader gestart. MM_PER_REV = {MM_PER_REV} mm/omwenteling")
    print("Eerste geldige meting wordt gebruikt als nulpositie (0° / 0 mm).")
    print("Stoppen met Ctrl+C.\n")

    try:
        while True:
            result = sensor.update()
            if result is not None:
                print(
                    f"Raw: {result['angle_raw']:4d} | "
                    f"CalDeg: {result['angle_deg_cal']:7.2f} | "
                    f"AbsDeg: {result['angle_deg_abs']:8.2f} | "
                    f"Pos(mm): {result['position_mm']:8.2f} | "
                    f"Speed(deg/s): {result['angular_velocity_dps']:7.2f}"
                )
            time.sleep(0.1)  # 100 ms, vergelijkbaar met Arduino
    except KeyboardInterrupt:
        print("\nStoppen...")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
