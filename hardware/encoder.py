# bijvoorbeeld in hardware/encoder.py

import yaml
from pathlib import Path
import smbus2  # zorg dat je dit hebt: pip install smbus2

# Pad naar config.yaml (pas aan als die ergens anders staat)
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

# AS5600 registers
AS5600_RAW_ANGLE_REG = 0x0C  # 0x0C (high) + 0x0D (low)
AS5600_RESOLUTION    = 4096  # 12-bit: 0..4095 → 0..360°


def _load_encoder_config():
    """Laad encoder-instellingen uit config.yaml."""
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f) or {}

    enc_cfg = (cfg.get("encoder") or {}).get("as5600") or {}

    bus_num     = enc_cfg.get("bus", 1)
    address     = enc_cfg.get("address", 0x36)
    zero_offset = float(enc_cfg.get("zero_offset_deg", 0.0))

    return bus_num, address, zero_offset


# Config inlezen en I2C-bus openen
_BUS_NUM, _ADDR, _ZERO_OFFSET_DEG = _load_encoder_config()
_bus = smbus2.SMBus(_BUS_NUM)


def _read_raw_angle() -> int:
    """
    Lees de ruwe 12-bit hoek uit de AS5600 (0..4095).
    """
    # Lees 2 bytes vanaf RAW_ANGLE register
    data = _bus.read_i2c_block_data(_ADDR, AS5600_RAW_ANGLE_REG, 2)
    raw = (data[0] << 8) | data[1]
    return raw & 0x0FFF  # alleen de onderste 12 bits


def read_encoder_angle_deg() -> float:
    """
    Geef de huidige encoderhoek in graden (0..360).
    Houdt rekening met een zero-offset uit config.yaml.
    """
    raw = _read_raw_angle()
    angle_deg = (raw / AS5600_RESOLUTION) * 360.0  # schaal naar graden

    # Zero-offset toepassen & binnen 0..360 houden
    angle_deg = (angle_deg - _ZERO_OFFSET_DEG) % 360.0
    return angle_deg
