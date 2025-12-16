from flask import Flask, render_template, request, jsonify
from core.gpio_singleton import gpio
from hardware.motor_controller import TransportMotor
from hardware.encoder import read_encoder_angle_deg


app = Flask(__name__)

motor = TransportMotor()

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
    
    
@app.route('/api/encoder', methods=['GET'])
def encoder_value():
    """
    Geeft de huidige encoderhoek in graden terug als JSON:
    { "angle": 123.4 }
    """
    try:
        angle = float(read_encoder_angle_deg())
    except Exception as e:
        print("Fout bij uitlezen encoder:", e)
        return jsonify(success=False, error=str(e)), 500

    return jsonify(success=True, angle=angle)
