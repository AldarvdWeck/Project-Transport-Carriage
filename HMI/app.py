from flask import Flask, render_template, request, jsonify
from core.gpio_singleton import gpio
from hardware.motor_controller import TransportMotor
from hardware.serial_reader import ArduinoSensorReader

from hardware.encoder_state import EncoderState
from hardware.homing2 import HomingController

app = Flask(__name__)

motor = TransportMotor()

arduino_reader = ArduinoSensorReader(baudrate=115200)
arduino_reader.start()

encoder_state = EncoderState(mm_per_rev=50.0, direction_sign=-1)

homing = HomingController(
    motor=motor,
    gpio=gpio,
    arduino_reader=arduino_reader,
    encoder_state=encoder_state,
    sensor_name="sensor_1",   # jouw inductiesensor
    direction="backward",     # richting naar sensor
    speed=0.4,
    timeout_s=10.0
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/automatic')
def automatic():
    return render_template('automatic.html')

@app.route('/manual')
def manual():
    return render_template('manual.html')

@app.route('/api/automatic/led', methods=['POST'])
def automatic_led():
    data = request.get_json(force=True)
    action = data.get('action')

    if action == 'start':
        gpio.on("status_led")
    elif action == 'stop':
        gpio.off("status_led")
    else:
        return jsonify(success=False, error="Unknown action"), 400

    return jsonify(success=True)

@app.route('/api/sensors/1', methods=['GET'])
def sensor_1_status():
    active = gpio.is_active("sensor_1")
    return jsonify(active=active)

@app.route('/api/manual/motor', methods=['POST'])
def manual_motor():
    """
    API endpoint om de motor in manual mode aan te sturen.
    Verwacht JSON zoals:
      { "direction": "forward", "action": "start", "speed": 0.6 }
    """
    data = request.get_json(force=True) or {}

    direction = data.get('direction')
    action = data.get('action', 'start')
    speed = float(data.get('speed', 0.6))  # default 60% duty

    try:
        if direction == 'forward':
            if action == 'start':
                motor.forward(speed)
            elif action == 'stop':
                motor.stop(brake=False)
            else:
                return jsonify(success=False, error="Unknown action"), 400

        elif direction == 'backward':
            if action == 'start':
                motor.backward(speed)
            elif action == 'stop':
                motor.stop(brake=False)
            else:
                return jsonify(success=False, error="Unknown action"), 400

        else:
            return jsonify(success=False, error="Unknown direction"), 400

        return jsonify(success=True)

    except Exception as e:
        # Handige debug als er iets misgaat
        print("Error in manual_motor:", e)
        return jsonify(success=False, error=str(e)), 500
    

# @app.route('/api/encoder', methods=['GET'])
# def encoder_value():
#     """
#     Geeft AS5600 hoek in graden terug:
#     { success: true, angle: 123.4 }
#     """
#     data = arduino_reader.get_latest()

#     if not data.get("ok") or data.get("angle_deg") is None:
#         return jsonify(success=False, error=data.get("error", "No data")), 500

#     return jsonify(success=True, angle=float(data["angle_deg"]))

@app.route('/api/encoder', methods=['GET'])
def encoder_value():
    data = arduino_reader.get_latest()

    if not data.get("ok") or data.get("angle_deg") is None:
        return jsonify(success=False, error=data.get("error", "No data")), 500

    raw = float(data["angle_deg"])

    # clamp_min_zero=True omdat home bij eindstop zit
    pos_mm = encoder_state.get_position_mm(raw, clamp_min_zero=True)

    return jsonify(success=True, position_mm=pos_mm, is_homed=encoder_state.is_homed())

    
@app.route('/api/homing/start', methods=['POST'])
def start_homing():
    started = homing.start()
    if not started:
        return jsonify(success=False, error="Homing already running"), 409
    return jsonify(success=True)

@app.route('/api/homing/status', methods=['GET'])
def homing_status():
    return jsonify(success=True, **homing.status())

    
@app.route('/api/potmeter', methods=['GET'])
def potmeter_value():
    """
    Geeft potmeter raw (0-1023) terug:
    { success: true, value: 512 }
    """
    data = arduino_reader.get_latest()

    if not data.get("ok") or data.get("pot_raw") is None:
        return jsonify(success=False, error=data.get("error", "No data")), 500

    return jsonify(success=True, value=int(data["pot_raw"]))

@app.route('/api/homing/cancel', methods=['POST'])
def cancel_homing():
    ok = homing.cancel()
    if not ok:
        return jsonify(success=False, error="Homing not running"), 409
    return jsonify(success=True)
