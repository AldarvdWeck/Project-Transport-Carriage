from flask import Flask, render_template, request, jsonify
from core.gpio_singleton import gpio

app = Flask(__name__)

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