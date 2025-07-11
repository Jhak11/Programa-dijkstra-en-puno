# grafo/osm_datos.py
import osmnx as ox
import json
import os
from shapely.geometry import Point
from osmnx.distance import nearest_nodes
import requests
from shapely.geometry import Polygon, Point
from osmnx import distance



def obtener_grafo_ciudad(ciudad):
    """
    Carga el grafo desde archivo si existe, si no lo descarga y lo guarda.
    Usa nombres como 'puno.graphml', 'cusco.graphml', etc.
    """
    try:
        ox.settings.use_cache = True
        ox.settings.log_console = False

        # Obtener nombre base (ej. "Puno, Peru" → "puno")
        nombre_base = ciudad.lower().split(",")[0].strip()
        nombre_archivo = f"{nombre_base}.graphml"
        ruta_archivo = os.path.join("datos", nombre_archivo)

        # Si ya existe, cargar desde archivo
        if os.path.exists(ruta_archivo):
            print(f"Cargando grafo desde archivo: {ruta_archivo}")
            G = ox.load_graphml(ruta_archivo)
        else:
            print(f"Descargando grafo de {ciudad}...")
            G = ox.graph_from_place(ciudad, network_type='drive')
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)

            # Guardar para futuras cargas
            os.makedirs("datos", exist_ok=True)
            ox.save_graphml(G, filepath=ruta_archivo)
            print(f"Grafo guardado en {ruta_archivo}")

        print(f"Grafo cargado: {len(G.nodes)} nodos, {len(G.edges)} aristas")
        return G

    except Exception as e:
        print(f"Error al cargar o descargar grafo: {e}")
        return None


def obtener_hospitales():
    """
    Extrae hospitales y clínicas dentro del área urbana de Puno, usando Overpass y un polígono definido manualmente.
    """
    try:
        print("📡 Buscando hospitales en Puno...")

        # Polígono manual aproximado de la ciudad de Puno (en orden horario o antihorario)
        polygon = Polygon([
            (-70.0364, -15.8235),
            (-70.0364, -15.8510),
            (-70.0100, -15.8510),
            (-70.0100, -15.8235),
            (-70.0364, -15.8235)  # cerrar polígono
        ])

        # Obtener bounding box
        minx, miny, maxx, maxy = polygon.bounds

        # Consulta Overpass
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
          way["amenity"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
          relation["amenity"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
          node["healthcare"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
          way["healthcare"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
          relation["healthcare"~"hospital|clinic"]({miny},{minx},{maxy},{maxx});
        );
        out center;
        """

        url = "http://overpass-api.de/api/interpreter"
        r = requests.get(url, params={'data': query}, headers={'User-Agent': 'hospital-finder'})
        r.raise_for_status()
        data = r.json()

        hospitales = []
        for e in data.get("elements", []):
            lat = e.get("lat") or e.get("center", {}).get("lat")
            lon = e.get("lon") or e.get("center", {}).get("lon")
            if lat and lon:
                punto = Point(lon, lat)
                if polygon.contains(punto):
                    nombre = e.get("tags", {}).get("name", f"Hospital {len(hospitales)+1}")
                    hospitales.append({
                        "nombre": nombre,
                        "lat": round(lat, 8),
                        "lon": round(lon, 8)
                    })

        print(f"✅ {len(hospitales)} hospitales encontrados en Puno")
        return hospitales

    except Exception as e:
        print(f"❌ Error al obtener hospitales: {e}")
        return []

def guardar_hospitales(hospitales, archivo='datos/hospitales.json'):
    """
    Guarda la lista de hospitales en un archivo JSON
    """
    try:
        os.makedirs(os.path.dirname(archivo), exist_ok=True)
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(hospitales, f, ensure_ascii=False, indent=2)
        print(f"💾 Hospitales guardados en {archivo}")
        return True
    except Exception as e:
        print(f"❌ Error al guardar hospitales: {e}")
        return False

def cargar_hospitales(archivo='datos/hospitales.json'):
    """
    Carga la lista de hospitales desde un archivo JSON
    """
    try:
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                hospitales = json.load(f)
            print(f"📂 Hospitales cargados desde {archivo}")
            return hospitales
        else:
            print(f"⚠️ Archivo {archivo} no encontrado")
            return []
    except Exception as e:
        print(f"❌ Error al cargar hospitales: {e}")
        return []
    

import requests

def obtener_ubicacion_actual():
    try:
        r = requests.get("http://localhost:5000/ubicacion")
        if r.status_code == 200:
            return r.json()
    except:
        return None

def obtener_nodos_principales(G, incluir_ubicacion_actual=True):
    """
    Devuelve nodos correspondientes a ubicaciones importantes de Puno
    y opcionalmente la ubicación actual del usuario.
    """
    try:
        lugares = [
            {"nombre": "Universidad Nacional del Altiplano", "lat": -15.8242768, "lon": -70.0161264},
            {"nombre": "Parque Pino", "lat": -15.8378073, "lon": -70.0280672},
            {"nombre": "Mercado Central", "lat": -15.8375174, "lon": -70.0266090},
            {"nombre": "Av. Simón Bolívar", "lat": -15.8443961, "lon": -70.0185250},
            {"nombre": "Mirador Kuntur Wasi", "lat": -15.8471356, "lon": -70.0299513}
        ]

        # Si se solicita, agregar la ubicación actual
        if incluir_ubicacion_actual:
            ubicacion = obtener_ubicacion_actual()
            if ubicacion:
                lugares.append({
                    "nombre": "Ubicación actual",
                    "lat": ubicacion["lat"],
                    "lon": ubicacion["lon"]
                })

        nodos_principales = []

        for lugar in lugares:
            nodo = distance.nearest_nodes(G, X=lugar["lon"], Y=lugar["lat"])
            nodo_data = G.nodes[nodo]
            nodos_principales.append({
                "id": nodo,
                "nombre": lugar["nombre"],
                "lat": nodo_data["y"],
                "lon": nodo_data["x"]
            })

        return nodos_principales

    except Exception as e:
        print(f"Error al obtener nodos principales: {e}")
        return []
    