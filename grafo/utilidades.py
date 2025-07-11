# grafo/utilidades.py
import osmnx as ox
import math

def nodo_mas_cercano(G, lat, lon):
    """
    Encuentra el nodo más cercano a una coordenada dada
    """
    try:
        return ox.distance.nearest_nodes(G, lon, lat)
    except Exception as e:
        print(f"Error al encontrar nodo más cercano: {e}")
        return None

def coordenadas_nodo(G, nodo):
    """
    Obtiene las coordenadas de un nodo
    """
    try:
        return G.nodes[nodo]['y'], G.nodes[nodo]['x']
    except Exception as e:
        print(f"Error al obtener coordenadas del nodo: {e}")
        return None, None

def distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en línea recta entre dos puntos usando la fórmula de Haversine
    """
    R = 6371  # Radio de la Tierra en km
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c * 1000  # Convertir a metros

def formatear_distancia(distancia_metros):
    """
    Formatea la distancia en metros a un formato legible
    """
    if distancia_metros < 1000:
        return f"{distancia_metros:.0f} m"
    else:
        return f"{distancia_metros/1000:.2f} km"

def formatear_tiempo(tiempo_segundos):
    """
    Formatea el tiempo en segundos a un formato legible
    """
    if tiempo_segundos < 60:
        return f"{tiempo_segundos:.0f} seg"
    elif tiempo_segundos < 3600:
        minutos = tiempo_segundos / 60
        return f"{minutos:.1f} min"
    else:
        horas = tiempo_segundos / 3600
        return f"{horas:.1f} h"

def obtener_ruta_coordenadas(G, ruta_nodos):
    """
    Convierte una ruta de nodos a una lista de coordenadas
    """
    try:
        coordenadas = []
        for nodo in ruta_nodos:
            lat, lon = coordenadas_nodo(G, nodo)
            if lat is not None and lon is not None:
                coordenadas.append([lon, lat])  # Mapbox usa [lon, lat]
        return coordenadas
    except Exception as e:
        print(f"Error al obtener coordenadas de la ruta: {e}")
        return []

def validar_coordenadas(lat, lon):
    """
    Valida que las coordenadas estén en rangos válidos
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    except ValueError:
        return False

def obtener_bounds_ruta(coordenadas):
    """
    Obtiene los límites (bounds) de una ruta para centrar el mapa
    """
    if not coordenadas:
        return None
    
    lats = [coord[1] for coord in coordenadas]
    lons = [coord[0] for coord in coordenadas]
    
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons)
    }