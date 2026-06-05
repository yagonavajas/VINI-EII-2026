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
Consultas relacionadas con rendimiento y datos de jugadores individuales:

• Precio de Goles: Muestra los jugadores con mayor salario anual, el total de goles anotados y el coste por gol (salario / goles).
• Más goles en un partido: Lista a los máximos goleadores en un partido registrados en el sistema.
• Veteranos con participación: Filtra y muestra a los jugadores de mayor edad y sus estadísticas.
        """
    },
    "Equipos": {
        "title": "Pestaña de Equipos",
        "description": """
Consultas sobre clubes, rendimiento internacional y aspectos tácticos:

• Ganadores de la UEFA Champions League: Muestra los campeones históricos de Europa junto con su valoración general (overall) y su formación táctica habitual.
• Eficacia de Goles vs Expected Goals: Compara los goles reales anotados con los goles esperados (xG) para identificar qué equipos son los más efectivos o ineficientes de cara a portería.
• Análisis de Formaciones Tácticas: Detalla los esquemas tácticos más utilizados por los distintos conjuntos.
        """
    },
    "Partidos": {
        "title": "Pestaña de Partidos",
        "description": """
Análisis estadístico de enfrentamientos directos y variables de juego:

• Goles en Casa vs Fuera: Evalúa la ventaja de la localía analizando cómo cambian los resultados cuando los equipos juegan en su propio estadio versus cuando son visitantes.
• Partidos con más Tarjetas Rojas: Muestra las estadísticas de expulsiones en los encuentros y su impacto en el juego.
• Mayor diferencia de cuotas y sorpresa en el resultado: Analiza las brechas en el marcador y la disparidad de nivel en los diferentes partidos.
        """
    },
    "Competiciones": {
        "title": "Pestaña de Competiciones",
        "description": """
Estadísticas globales a nivel de torneos y análisis predictivo:

• Porcentaje de aciertos por casa de apuestas: Muestra métricas de cuotas de apuesta agrupados por casa de apuesta.
• Análisis de Campeones de las 5 grandes ligas: Revisa las estadísticas históricas de los ganadores de cada competición.
• Cambios en el rendimiento de los campeones del año siguiente: Examina como varían de un año a otro los equipos campeones.
        """
    },
    "Especial": {
        "title": "Pestaña Especial - Consultas Avanzadas",
        "description": """
Herramientas interactivas y visuales para explorar datos específicos a demanda:

SECCIÓN DE EQUIPOS:
• Búsqueda predictiva: Filtra clubes dinámicamente escribiendo su nombre.
• Ver Equipaciones: Permite visualizar de forma gráfica los uniformes y camisetas del club seleccionado.
• Mostrar Plantilla: Genera una tabla detallada con los jugadores del equipo y sus estadísticas actuales.

SECCIÓN DE JUGADORES:
• Búsqueda predictiva: Filtra futbolistas dinámicamente escribiendo su nombre.
• Ver Foto: Descarga y renderiza en tiempo real la imagen oficial del jugador desde Sofifa.
• Ver Estadísticas: Desglosa los atributos técnicos, físicos y numéricos detallados del perfil del jugador.
        """
    },
    "Consultas personalizadas": {
        "title": "Pestaña de Consultas Personalizadas",
        "description": """
Editor avanzado para escribir tus propias consultas SPARQL:

• Escribe tu consulta: Área de texto libre con soporte completo para la sintaxis SPARQL.
• Ejecutar Consulta: Lanza la petición directamente contra la base de datos de conocimiento.
• Resultados: Renderiza una tabla dinámica que ajusta automáticamente sus columnas según las variables devueltas.

Incluye control de excepciones para capturar errores de sintaxis o conexión con mensajes descriptivos.
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
        text += f"{tab_info['title']}\n"
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
