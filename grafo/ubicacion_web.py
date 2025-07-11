# grafo/ubicacion_web.py
from flask import Flask, request, render_template, jsonify
import threading

ubicacion = {}

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    return render_template('mapa_ubicacion.html')

@app.route('/ubicacion', methods=['POST'])
def recibir_ubicacion():
    global ubicacion
    ubicacion = request.json
    print(f"📍 Ubicación actualizada: {ubicacion}")
    return "OK"

@app.route('/ubicacion', methods=['GET'])
def obtener_ubicacion():
    return jsonify(ubicacion)

def iniciar_servidor():
    threading.Thread(target=lambda: app.run(port=5000, debug=False), daemon=True).start()
