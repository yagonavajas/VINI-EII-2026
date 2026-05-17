"""
Módulo de menú y ayuda para la aplicación VINI
Contiene la configuración del menú superior y textos de ayuda
"""

# ============================================================================
# INFORMACIÓN DE PESTAÑAS
# ============================================================================

TABS_HELP = {
    "Jugadores": {
        "title": "Pestaña de Jugadores",
        "description": """
Consultas relacionadas con jugadores individuales:

• Precio de Goles: Muestra los 10 jugadores con mayor salario anual, 
  el total de goles anotados y el coste por gol (salario / goles).
  
Útil para analizar la relación entre inversión en salarios y 
rendimiento goleador.
        """
    },
    "Equipos": {
        "title": "Pestaña de Equipos",
        "description": """
Consultas sobre equipos y sus estadísticas agregadas:

• Ganadores de la UEFA Champions League: Muestra los campeones de Europa
  con su overall general y formación táctica.
  
• Eficacia de Goles vs Expected Goals: Analiza qué equipos son más 
  efectivos/inefectivos comparando goles reales con goles esperados.
  
Útil para ver performance de equipos a nivel europeo y eficiencia ofensiva.
        """
    },
    "Partidos": {
        "title": "Pestaña de Partidos",
        "description": """
Consultas relacionadas con partidos individuales y estadísticas en vivo.

⚠️ Esta pestaña aún no tiene consultas implementadas.
Placeholder para futuras análisis de:
- Resultados de partidos
- Estadísticas por jornada
- Comparativas entre equipos
        """
    },
    "Competiciones": {
        "title": "Pestaña de Competiciones",
        "description": """
Consultas sobre torneos y competiciones.

⚠️ Esta pestaña aún no tiene consultas implementadas.
Placeholder para futuras análisis de:
- Clasificaciones de ligas
- Evolución de competiciones
- Estadísticas por competición
        """
    },
    "Especial": {
        "title": "Pestaña Especial - Consultas Avanzadas",
        "description": """
Herramientas interactivas para explorar datos específicos:

SECCIÓN DE EQUIPOS:
• Busca un equipo: Escribe para filtrar equipos por nombre y año
• Ver Equipaciones: Muestra todas las camisetas/uniformes del equipo
• Mostrar Plantilla: Tabla con jugadores del equipo y sus estadísticas

SECCIÓN DE JUGADORES:
• Busca un jugador: Escribe para filtrar jugadores por nombre y año
• Ver Foto: Descarga y muestra la foto del jugador desde Sofifa

Ideal para exploración interactiva y visualización de datos específicos.
        """
    },
    "Consultas personalizadas": {
        "title": "Pestaña de Consultas Personalizadas",
        "description": """
Editor avanzado para escribir tus propias consultas SPARQL:

• Escribe tu consulta: Área de texto para introducir SPARQL válido
• Ejecutar Consulta: Lanza la consulta contra la base de datos
• Resultados: Tabla dinámica con todos los resultados

Características:
- Soporte completo de sintaxis SPARQL
- Configuración automática de columnas según resultados
- Manejo de errores con mensajes descriptivos

Perfecto para análisis personalizados y experimentación.
        """
    }
}

# ============================================================================
# TEXTOS DE AYUDA GENERAL
# ============================================================================

ABOUT_APP = """
VINI - Consultas de Fútbol
v1.0

Una aplicación de escritorio para consultar datos de fútbol almacenados 
en un triple store RDF usando SPARQL como lenguaje de consulta.

CARACTERÍSTICAS:
✓ Consultas predefinidas sobre campeones, eficacia y jugadores
✓ Búsqueda interactiva de equipos y jugadores
✓ Visualización de equipaciones (camisetas)
✓ Galería de fotos de jugadores
✓ Consultas SPARQL personalizadas
✓ Editor de consultas SPARQL avanzado

DATOS DISPONIBLES:
• Equipos y temporadas (2016-2020)
• Jugadores y sus estadísticas
• Partidos y resultados
• Competiciones (ligas europeas, Champions League)
• Estadísticas individuales y agregadas

FUENTES:
- Datos de jugadores: SoFIFA
- Datos de partidos y competiciones: Football Database
- Información de competiciones: Wikidata

DESARROLLADO CON:
- Python + Tkinter (interfaz)
- SPARQLWrapper (consultas)
- Apache Jena Fuseki (triple store)
- BeautifulSoup (web scraping de imágenes)
"""

HELP_SHORTCUTS = """
ATAJOS Y CONSEJOS:

BÚSQUEDA:
• En la pestaña "Especial", escribe en los combobox para filtrar
• Presiona Tab o Enter para confirmar selección
• Los resultados se actualizan mientras escribes

CONSULTAS:
• Todas las consultas predefinidas funcionan con botones directos
• Para queries personalizadas, escribe SPARQL válido
• Usa PREFIX vini: <http://vini-eii.org/> para acceder al namespace

INFORMACIÓN ÚTIL:
• Las imágenes se descargan desde Sofifa automáticamente
• Las fotos se muestran en máxima resolución disponible
• Las equipaciones se muestran en galería con navegación

TROUBLESHOOTING:
• Si una consulta falla, revisa la sintaxis SPARQL
• Fuseki debe estar activo en puerto 3030
• Si no cargan imágenes, verifica conexión a internet
"""

KEYBOARD_SHORTCUTS = {
    "Ctrl+Q": "Cerrar aplicación",
    "Tab": "Navegar entre campos",
    "Enter": "Confirmar selección en combobox",
    "Ctrl+A": "Seleccionar todo en editor de texto",
}

# ============================================================================
# FUNCIONES DE MENÚ
# ============================================================================

def get_tabs_help_text():
    """Retorna texto de ayuda formateado para todas las pestañas"""
    text = "AYUDA DE PESTAÑAS\n"
    text += "=" * 60 + "\n\n"
    
    for tab_name, tab_info in TABS_HELP.items():
        text += f"▪ {tab_info['title']}\n"
        text += f"{tab_info['description']}\n"
        text += "-" * 60 + "\n\n"
    
    return text

def get_help_text():
    """Retorna el texto de ayuda general"""
    text = ABOUT_APP + "\n\n"
    text += "=" * 60 + "\n\n"
    text += HELP_SHORTCUTS + "\n\n"
    text += "=" * 60 + "\n"
    text += "ATAJOS DE TECLADO:\n\n"
    
    for shortcut, description in KEYBOARD_SHORTCUTS.items():
        text += f"  {shortcut:15} → {description}\n"
    
    return text
