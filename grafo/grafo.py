# grafo/grafo.py
import networkx as nx
from .utilidades import coordenadas_nodo, formatear_distancia, formatear_tiempo, nodo_mas_cercano

class GrafoDijkstra:
    def __init__(self, G):
        self.G = G
    
    def rutas_dijkstra(self, nodo_origen, lista_destinos):
        """
        Calcula las rutas más cortas desde el origen a múltiples destinos usando Dijkstra
        """
        rutas = {}
        
        for destino in lista_destinos:
            try:
                # Calcular ruta más corta
                camino = nx.shortest_path(self.G, nodo_origen, destino, weight='length')
                longitud = nx.shortest_path_length(self.G, nodo_origen, destino, weight='length')
                
                # Calcular tiempo si está disponible
                tiempo = 0
                
                #try:
                    #tiempo = nx.shortest_path_length(self.G, nodo_origen, destino, weight='travel_time')
                #except:
                # Si no hay datos de tiempo, estimamos basado en velocidad promedio
                velocidad_promedio = 4.5  # km/h
                tiempo = ((longitud / 1000) / velocidad_promedio) * 3600  # segundos
                
                rutas[destino] = {
                    'camino': camino,
                    'longitud': longitud,
                    'tiempo': tiempo,
                    'longitud_formateada': formatear_distancia(longitud),
                    'tiempo_formateado': formatear_tiempo(tiempo)
                }
                
            except nx.NetworkXNoPath:
                print(f"No se encontró ruta al destino {destino}")
                continue
            except Exception as e:
                print(f"Error calculando ruta a {destino}: {e}")
                continue
        
        return rutas
    
    def encontrar_destino_mas_cercano(self, rutas):
        """
        Encuentra el destino más cercano basado en la distancia
        """
        if not rutas:
            return None
        
        destino_mas_cercano = min(rutas.keys(), key=lambda x: rutas[x]['longitud'])
        return destino_mas_cercano
    
    def obtener_estadisticas_rutas(self, rutas):
        """
        Obtiene estadísticas generales de las rutas calculadas
        """
        if not rutas:
            return None
        
        longitudes = [ruta['longitud'] for ruta in rutas.values()]
        tiempos = [ruta['tiempo'] for ruta in rutas.values()]
        
        return {
            'total_rutas': len(rutas),
            'distancia_minima': min(longitudes),
            'distancia_maxima': max(longitudes),
            'distancia_promedio': sum(longitudes) / len(longitudes),
            'tiempo_minimo': min(tiempos),
            'tiempo_maximo': max(tiempos),
            'tiempo_promedio': sum(tiempos) / len(tiempos)
        }
    
    def comparar_rutas(self, rutas, criterio='longitud'):
        """
        Compara y ordena las rutas según un criterio
        """
        if not rutas:
            return []
        
        rutas_ordenadas = sorted(
            rutas.items(),
            key=lambda x: x[1][criterio]
        )
        
        return rutas_ordenadas

def procesar_rutas_hospitales(G, nodo_origen, hospitales):
    """
    Función principal para procesar rutas a hospitales
    """
    
    # Crear instancia del grafo
    grafo_dijkstra = GrafoDijkstra(G)
    
    # Convertir coordenadas de hospitales a nodos
    nodos_hospitales = []
    hospitales_info = []
    
    for hospital in hospitales:
        nodo_hospital = nodo_mas_cercano(G, hospital['lat'], hospital['lon'])
        if nodo_hospital:
            nodos_hospitales.append(nodo_hospital)
            hospital_info = hospital.copy()
            hospital_info['nodo'] = nodo_hospital
            hospitales_info.append(hospital_info)
    
    # Calcular rutas
    rutas = grafo_dijkstra.rutas_dijkstra(nodo_origen, nodos_hospitales)
    
    # Encontrar hospital más cercano
    destino_mas_cercano = grafo_dijkstra.encontrar_destino_mas_cercano(rutas)
    
    # Combinar información de hospitales con rutas
    resultado = {
        'rutas': {},
        'hospitales_info': {},
        'destino_mas_cercano': destino_mas_cercano,
        'estadisticas': grafo_dijkstra.obtener_estadisticas_rutas(rutas)
    }
    
    for hospital_info in hospitales_info:
        nodo = hospital_info['nodo']
        if nodo in rutas:
            resultado['rutas'][nodo] = rutas[nodo]
            resultado['hospitales_info'][nodo] = hospital_info
    
    return resultado