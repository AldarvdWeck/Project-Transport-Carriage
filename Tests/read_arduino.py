import serial

# Pas dit aan indien nodig
PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

print("Verbonden met Arduino")



while True:
    line = ser.readline().decode("utf-8").strip()
    if not line:
        continue

    try:
        angle_deg, pot = line.split(",")
        angle_deg = float(angle_deg)
        pot = int(pot)

        print(f"AS5600: {angle_deg:.2f} deg | Potmeter: {pot}")

    except ValueError:
        print("Onverwachte data:", line)
