# mapa.py
import json
import os
from config import MAPBOX_API_KEY, COLORES, MAPA_CONFIG
from grafo.utilidades import obtener_ruta_coordenadas, coordenadas_nodo, obtener_bounds_ruta

def generar_mapa_html(G, nodo_origen, resultado_rutas, nombre_archivo='templates/mapa.html'):
    """
    Genera un archivo HTML con el mapa de rutas usando Mapbox GL JS
    """
    try:
        # Obtener coordenadas del origen
        lat_origen, lon_origen = coordenadas_nodo(G, nodo_origen)
        
        # Preparar datos para el mapa
        rutas_geojson = []
        marcadores = []
        
        # Agregar marcador de origen
        marcadores.append({
            'coordinates': [lon_origen, lat_origen],
            'title': 'Punto de Origen',
            'color': COLORES['marcador_origen']
        })
        
        # Procesar rutas
        destino_mas_cercano = resultado_rutas.get('destino_mas_cercano')
        
        for nodo_destino, ruta_info in resultado_rutas['rutas'].items():
            hospital_info = resultado_rutas['hospitales_info'][nodo_destino]
            
            # Obtener coordenadas de la ruta
            coordenadas_ruta = obtener_ruta_coordenadas(G, ruta_info['camino'])
            
            # Determinar color de la ruta
            color = COLORES['ruta_mas_corta'] if nodo_destino == destino_mas_cercano else COLORES['ruta_normal']
            
            # Crear GeoJSON para la ruta
            ruta_geojson = {
                'type': 'Feature',
                'properties': {
                    'title': hospital_info['nombre'],
                    'distance': ruta_info['longitud_formateada'],
                    'time': ruta_info['tiempo_formateado'],
                    'color': color,
                    'is_shortest': nodo_destino == destino_mas_cercano
                },
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coordenadas_ruta
                }
            }
            rutas_geojson.append(ruta_geojson)
            
            # Agregar marcador del hospital
            marcadores.append({
                'coordinates': [hospital_info['lon'], hospital_info['lat']],
                'title': hospital_info['nombre'],
                'description': f"Distancia: {ruta_info['longitud_formateada']}<br>Tiempo: {ruta_info['tiempo_formateado']}",
                'color': COLORES['marcador_destino'],
                'is_closest': nodo_destino == destino_mas_cercano
            })
        
        # Calcular centro del mapa
        todas_coordenadas = []
        for ruta in rutas_geojson:
            todas_coordenadas.extend(ruta['geometry']['coordinates'])
        
        if todas_coordenadas:
            bounds = obtener_bounds_ruta(todas_coordenadas)
            centro_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
            centro_lon = (bounds['min_lon'] + bounds['max_lon']) / 2
        else:
            centro_lat = lat_origen
            centro_lon = lon_origen
        
        # Generar HTML
        html_content = generar_html_template(
            rutas_geojson, 
            marcadores, 
            centro_lat, 
            centro_lon,
            resultado_rutas.get('estadisticas', {})
        )
        
        # Guardar archivo
        os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Mapa generado: {nombre_archivo}")
        return nombre_archivo
        
    except Exception as e:
        print(f"Error generando mapa: {e}")
        return None

def generar_html_template(rutas_geojson, marcadores, centro_lat, centro_lon, estadisticas):
    """
    Genera el contenido HTML del mapa
    """
    
    
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8' />
    <title>Rutas a Hospitales - Dijkstra</title>
    <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
    <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
    <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .mapboxgl-popup-content {{ max-width: 300px; }}
        .info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 5px;
            max-width: 300px;
            z-index: 1000;
        }}
        .route-info {{
            margin: 5px 0;
            padding: 5px;
            border-radius: 3px;
        }}
        .shortest-route {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }}
        .normal-route {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 3px;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div id='map'></div>
    
    <div class='info-panel'>
        <h3>Rutas a Hospitales</h3>
        <div id='route-list'></div>
        <div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #ccc;'>
            <strong>Estadísticas:</strong><br>
            <small>
                Rutas calculadas: {estadisticas.get('total_rutas', 0)}<br>
                Distancia mínima: {estadisticas.get('distancia_minima', 0):.0f}m<br>
                Distancia máxima: {estadisticas.get('distancia_maxima', 0):.0f}m
            </small>
        </div>
    </div>
    
    <div class='legend'>
        <div class='legend-item'>
            <div class='legend-color' style='background-color: {COLORES['ruta_mas_corta']};'></div>
            <span>Ruta más corta</span>
        </div>
        <div class='legend-item'>
            <div class='legend-color' style='background-color: {COLORES['ruta_normal']};'></div>
            <span>Otras rutas</span>
        </div>
        <div class='legend-item'>
            <div class='legend-color' style='background-color: {COLORES['marcador_origen']}; height: 10px; border-radius: 50%;'></div>
            <span>Origen</span>
        </div>
        <div class='legend-item'>
            <div class='legend-color' style='background-color: {COLORES['marcador_destino']}; height: 10px; border-radius: 50%;'></div>
            <span>Hospitales</span>
        </div>
    </div>

    <script>
        mapboxgl.accessToken = '{MAPBOX_API_KEY}';
        
        const map = new mapboxgl.Map({{
            container: 'map',
            style: '{MAPA_CONFIG['estilo_mapa']}',
            center: [{centro_lon}, {centro_lat}],
            zoom: {MAPA_CONFIG['zoom_inicial']}
        }});

        

        
        map.on('load', function() {{
            // Agregar rutas
            const rutasData = {json.dumps(rutas_geojson)};
            const marcadoresData = {json.dumps(marcadores)};
            
            // Agregar fuente de datos para rutas
            map.addSource('rutas', {{
                'type': 'geojson',
                'data': {{
                    'type': 'FeatureCollection',
                    'features': rutasData
                }}
            }});
        
            
            // Agregar capa de rutas
            map.addLayer({{
                'id': 'rutas',
                'type': 'line',
                'source': 'rutas',
                'layout': {{
                    'line-join': 'round',
                    'line-cap': 'round'
                }},
                'paint': {{
                    'line-color': ['get', 'color'],
                    'line-width': [
                        'case',
                        ['get', 'is_shortest'],
                        4,
                        2
                    ],
                    'line-opacity': 0.8
                }}
            }});
            
            // Agregar marcadores
            marcadoresData.forEach(function(marcador) {{
                const el = document.createElement('div');
                el.className = 'marker';
                el.style.backgroundColor = marcador.color;
                el.style.width = marcador.is_closest ? '15px' : '10px';
                el.style.height = marcador.is_closest ? '15px' : '10px';
                el.style.borderRadius = '50%';
                el.style.border = '2px solid white';
                el.style.boxShadow = '0 0 5px rgba(0,0,0,0.3)';
                
                const popup = new mapboxgl.Popup({{ offset: 25 }})
                    .setHTML(`<h3>${{marcador.title}}</h3>${{marcador.description || ''}}`);
                
                new mapboxgl.Marker(el)
                    .setLngLat(marcador.coordinates)
                    .setPopup(popup)
                    .addTo(map);
            }});

            
            
            // Agregar información de rutas al panel
            const routeList = document.getElementById('route-list');
            rutasData.forEach(function(ruta) {{
                const routeDiv = document.createElement('div');
                routeDiv.className = `route-info ${{ruta.properties.is_shortest ? 'shortest-route' : 'normal-route'}}`;
                routeDiv.innerHTML = `
                    <strong>${{ruta.properties.title}}</strong><br>
                    <small>Distancia: ${{ruta.properties.distance}}</small><br>
                    <small>Tiempo: ${{ruta.properties.time}}</small>
                    ${{ruta.properties.is_shortest ? '<br><small><strong>★ MÁS CERCANO</strong></small>' : ''}}
                `;
                routeList.appendChild(routeDiv);
            }});
            
            // Popup para rutas
            map.on('click', 'rutas', function(e) {{
                const properties = e.features[0].properties;
                new mapboxgl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <h3>${{properties.title}}</h3>
                        <p>Distancia: ${{properties.distance}}</p>
                        <p>Tiempo: ${{properties.time}}</p>
                        ${{properties.is_shortest ? '<p><strong>★ Ruta más corta</strong></p>' : ''}}
                    `)
                    .addTo(map);
            }});
            
            // Cambiar cursor al pasar sobre rutas
            map.on('mouseenter', 'rutas', function() {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'rutas', function() {{
                map.getCanvas().style.cursor = '';
            }});
        }});
    </script>
</body>
</html>
    """
    
    return html_template

def generar_mapa_simple(lat, lon, nombre_archivo='templates/mapa_simple.html'):
    """
    Genera un mapa simple para mostrar una ubicación
    """
    html_simple = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8' />
    <title>Mapa Simple</title>
    <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
    <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
    <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
    </style>
</head>
<body>
    <div id='map'></div>
    <script>
        mapboxgl.accessToken = '{MAPBOX_API_KEY}';
        
        const map = new mapboxgl.Map({{
            container: 'map',
            style: '{MAPA_CONFIG['estilo_mapa']}',
            center: [{lon}, {lat}],
            zoom: {MAPA_CONFIG['zoom_inicial']}
        }});

        new mapboxgl.Marker()
            .setLngLat([{lon}, {lat}])
            .addTo(map);
    </script>
</body>
</html>
    """
    
    try:
        os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(html_simple)
        return nombre_archivo
    except Exception as e:
        print(f"Error generando mapa simple: {e}")
        return None