from time import sleep
from core.linearaxis import LinearAxisController


def main():
    controller = LinearAxisController()

    try:
        print("Homing...")
        if not controller.home():
            raise RuntimeError("Homing mislukt")

        print("Homing OK")

        success = controller.goto_position_mm(
            150.0,
            speed=0.5,
            timeout_s=20.0,
        )

        print("Goto 150 mm:", "OK" if success else "TIMEOUT")
        sleep(1.0)

        # Voorbeeld stations
        # controller.move_between_station_ids(1, 3)
        # print("Stations verplaatst")

    except Exception as e:
        print("Fout:", e)

    finally:
        controller.motor.stop(brake=True)
        print("Motor gestopt")


if __name__ == "__main__":
    main()
