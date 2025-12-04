from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    """Hoofd pagina"""
    return render_template('index.html')

@app.route('/automatic')
def automatic():
    """Automatische modus pagina"""
    return render_template('automatic.html')

@app.route('/manual')
def manual():
    """Handmatige modus pagina"""
    return render_template('manual.html')

if __name__ == '__main__':
    print("Transport HMI Server wordt gestart op http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)