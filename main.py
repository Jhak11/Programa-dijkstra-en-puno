# main.py
"""
Aplicación de Rutas a Hospitales usando Algoritmo de Dijkstra
Autor: Sistema de Navegación Médica
Descripción: Encuentra las rutas más cortas a hospitales usando datos de OpenStreetMap
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from grafo import ubicacion_web


# Agregar el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.ventana import VentanaPrincipal
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de tener instaladas todas las dependencias:")
    print("pip install PyQt5 PyQtWebEngine osmnx networkx folium")
    sys.exit(1)

class SplashScreen(QSplashScreen):
    """
    Pantalla de carga inicial
    """
    def __init__(self):
        # Crear un pixmap simple para la pantalla de carga
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.white)
        super().__init__(pixmap)
        
        # Configurar el texto
        font = QFont("Arial", 14, QFont.Bold)
        self.setFont(font)
        
        # Mostrar mensaje inicial
        self.showMessage("Cargando Aplicación de Rutas...", 
                        Qt.AlignCenter | Qt.AlignBottom, 
                        Qt.black)

def verificar_dependencias():
    """
    Verifica que todas las dependencias estén instaladas
    """
    dependencias_requeridas = [
        'osmnx',
        'networkx',
        'PyQt5',
        'shapely',
        'requests'
    ]
    
    dependencias_faltantes = []
    
    for dep in dependencias_requeridas:
        try:
            __import__(dep)
        except ImportError:
            dependencias_faltantes.append(dep)
    
    if dependencias_faltantes:
        mensaje = "Dependencias faltantes:\n\n"
        for dep in dependencias_faltantes:
            mensaje += f"- {dep}\n"
        mensaje += "\nInstala las dependencias con:\n"
        mensaje += "pip install " + " ".join(dependencias_faltantes)
        
        return False, mensaje
    
    return True, "Todas las dependencias están instaladas"

def verificar_configuracion():

    # Crear directorios necesarios
    directorios = ['datos', 'templates', 'ui', 'grafo']
    for directorio in directorios:
        if not os.path.exists(directorio):
            try:
                os.makedirs(directorio)
                print(f"Directorio creado: {directorio}")
            except Exception as e:
                return False, f"Error creando directorio {directorio}: {e}"
    
    return True, "Configuración válida"

def main():
    """
    Función principal de la aplicación
    """
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas a Hospitales - Dijkstra")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Sistema de Navegación Médica")
    
    # Pantalla de carga
    splash = SplashScreen()
    splash.show()
    
    # Procesar eventos para mostrar la pantalla de carga
    app.processEvents()
    
    try:
        # Verificar dependencias
        splash.showMessage("Verificando dependencias...", 
                          Qt.AlignCenter | Qt.AlignBottom, 
                          Qt.black)
        app.processEvents()
        
        deps_ok, deps_msg = verificar_dependencias()
        if not deps_ok:
            splash.close()
            QMessageBox.critical(None, "Error de Dependencias", deps_msg)
            return 1
        
        # Verificar configuración
        splash.showMessage("Verificando configuración...", 
                          Qt.AlignCenter | Qt.AlignBottom, 
                          Qt.black)
        app.processEvents()
        
        config_ok, config_msg = verificar_configuracion()
        if not config_ok:
            splash.close()
            QMessageBox.warning(None, "Error de Configuración", config_msg)
            return 1
        
        # Inicializar ventana principal
        splash.showMessage("Iniciando interfaz...", 
                          Qt.AlignCenter | Qt.AlignBottom, 
                          Qt.black)
        app.processEvents()
        # Iniciar el servidor Flask que recibirá la ubicación desde navegador
        splash.showMessage("Iniciando servicio de ubicación...", Qt.AlignCenter | Qt.AlignBottom, Qt.black)
        ubicacion_web.iniciar_servidor()
        
        ventana = VentanaPrincipal()
        
        # Cerrar pantalla de carga después de un breve delay
        QTimer.singleShot(2000, splash.close)
        QTimer.singleShot(2000, ventana.show)
        
        # Ejecutar aplicación
        return app.exec_()
        
    except Exception as e:
        splash.close()
        error_msg = f"Error iniciando la aplicación:\n{str(e)}"
        print(error_msg)
        QMessageBox.critical(None, "Error Fatal", error_msg)
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAplicación terminada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error no controlado: {e}")
        sys.exit(1)