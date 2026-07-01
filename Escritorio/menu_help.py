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

def get_data_model_help_text():
    """Retorna el texto de ayuda completo del modelo de datos con la estructura exacta de subgrafos"""
    text = "MODELO DE DATOS - ONTOLOGÍA Y SUBGRAFOS\n"
    text += "=" * 60 + "\n\n"
    text += "La ontología define detalladamente los conceptos, relaciones y atributos organizados en 7 subgrafos.\n\n"
    text += "1.1.1 Subgrafo 1, Teams graph\n"
    text += "1.1.1.1 Entidades del grafo\n"
    text += "- Team: Representa al club o equipo de fútbol de forma genérica e histórica, independientemente de la temporada. Es el nodo base que unifica el histórico de un club.\n"
    text += "- TeamSeason: Entidad temporal central que representa a un equipo de fútbol modelado específicamente en un año o temporada concreta. Alberga las estadísticas tácticas y técnicas del club en ese periodo.\n"
    text += "- Season: Representa el año o temporada temporal cronológica bajo la cual se evalúan las métricas.\n"
    text += "- League: Representa la competición o liga doméstica en la que participa el equipo durante una temporada determinada.\n"
    text += "- Country: Entidad geográfica que identifica el país de procedencia o de la liga en la que compite el club.\n\n"
    text += "1.1.1.2 Relaciones entre entidades\n"
    text += "- hasSeason (Team -> TeamSeason): Conecta el nodo genérico de un equipo con su correspondiente instancia temporal. Permite ramificar el histórico de un mismo club a lo largo de los años.\n"
    text += "- inSeason (TeamSeason -> Season): Vincula el rendimiento del equipo en un periodo específico con la entidad cronológica global de la temporada basada en el año.\n"
    text += "- hasCountry (TeamSeason -> Country): Relaciona al equipo de esa temporada con su país de origen, permitiendo segmentaciones geográficas.\n"
    text += "- playsInLeague (TeamSeason -> League): Conecta la instancia del equipo en una temporada con la liga o competición en la que disputó sus partidos ese año concreto.\n\n"
    text += "1.1.1.3 Atributos de las entidades\n"
    text += "- TeamSeason -> name (String / Literal): Nombre comercial completo del equipo en esa temporada.\n"
    text += "- TeamSeason -> url (String / Literal): Enlace web oficial a la ficha del equipo en la plataforma SoFifa.\n"
    text += "- TeamSeason -> formation (String / Literal): Táctica o alineación preferente utilizada.\n"
    text += "- TeamSeason -> year (Integer / Literal): Año cronológico correspondiente a la temporada actual del registro.\n"
    text += "- TeamSeason -> overall (Integer / Literal): Valoración media general del rendimiento del equipo.\n"
    text += "- TeamSeason -> attack (Integer / Literal): Puntuación del rendimiento global de la línea ofensiva.\n"
    text += "- TeamSeason -> midfield (Integer / Literal): Puntuación del rendimiento global del centro del campo.\n"
    text += "- TeamSeason -> defence (Integer / Literal): Puntuación del rendimiento global de la línea defensiva.\n"
    text += "- TeamSeason -> transfer_budget (Long / Literal): Presupuesto disponible en el club para fichajes e incorporaciones.\n"
    text += "- TeamSeason -> club_worth (Long / Literal): Valor de mercado total estimado del club de fútbol.\n"
    text += "- TeamSeason -> speed (Integer / Literal): Métrica táctica que mide la velocidad de los jugadores.\n"
    text += "- TeamSeason -> dribbling (Integer / Literal): Métrica de la capacidad colectiva de regate y conducción.\n"
    text += "- TeamSeason -> passing (Integer / Literal): Métrica que evalúa la precisión y estilo de los pases del plantel.\n"
    text += "- TeamSeason -> positioning (String / Literal): Atributo que define la libertad o rigidez posicional del equipo.\n"
    text += "- TeamSeason -> crossing (Integer / Literal): Puntuación colectiva de efectividad en centros al área.\n"
    text += "- TeamSeason -> shooting (Integer / Literal): Puntuación de efectividad en tiros a puerta y finalización.\n"
    text += "- TeamSeason -> aggression (Integer / Literal): Nivel de agresividad defensiva y presión física colectiva.\n"
    text += "- TeamSeason -> pressure (Integer / Literal): Altura y nivel de la línea de presión táctica ante la salida rival.\n"
    text += "- TeamSeason -> team_width (Integer / Literal): Amplitud táctica del equipo sobre el terreno de juego (ancho).\n"
    text += "- TeamSeason -> defender_line (Integer / Literal): Configuración o comportamiento de la línea defensiva.\n"
    text += "- TeamSeason -> domestic_prestige (Integer / Literal): Reputación o prestigio del club dentro de su propia liga local.\n"
    text += "- TeamSeason -> international_prestige (Integer / Literal): Reputación o prestigio del club a nivel continental/mundial.\n"
    text += "- TeamSeason -> players (Integer / Literal): Cantidad total de jugadores registrados en la plantilla esa temporada.\n"
    text += "- TeamSeason -> starting_xi_avg_age (Float / Literal): Edad promedio de los 11 jugadores titulares habituales.\n"
    text += "- TeamSeason -> whole_team_avg_age (Float / Literal): Edad promedio de la totalidad de la plantilla del equipo.\n"
    text += "\n\n"
    text += "1.1.2 Subgrafo 2, Competitions graph\n"
    text += "1.1.2.1 Entidades del grafo\n"
    text += "- CompetitionWinner: Entidad central de tipo evento o relación n-aria que representa el suceso histórico y específico de ganar un campeonato o copa en un año determinado.\n"
    text += "- Team: Representa al club o equipo de fútbol que se proclama vencedor.\n"
    text += "- Competition: Representa el torneo, copa o campeonato específico.\n"
    text += "- Season: Entidad cronológica global que identifica el año de la edición del torneo.\n"
    text += "- Country: Entidad geográfica que identifica el país donde se disputa o al que pertenece la competición ganada.\n\n"
    text += "1.1.2.2 Relaciones entre entidades\n"
    text += "- competition (CompetitionWinner -> Competition): Conecta el evento del triunfo con el torneo o campeonato específico que se ha disputado.\n"
    text += "- winningTeam (CompetitionWinner -> Team): Vincula el evento de la victoria con el club que se ha coronado campeón.\n"
    text += "- country (CompetitionWinner -> Country): Relaciona el evento del campeonato con el marco geográfico o país donde tiene origen.\n"
    text += "- season (CompetitionWinner -> Season): Enlaza el evento con la temporada temporal o año cronológico exacto en el que ocurrió.\n"
    text += "- wonCompetition (Team -> CompetitionWinner): Relación inversa que permite conocer desde la perspectiva del club qué títulos o eventos de victoria posee en su palmarés.\n"
    text += "- wonBy (Competition -> CompetitionWinner): Relación inversa que indica qué evento de victoria o edición histórica de campeones le pertenece a una competición concreta.\n\n"
    text += "1.1.2.3 Atributos de las entidades\n"
    text += "- Competition -> competitionName (String / Literal): Nombre oficial de la competición tal como está registrada en Wikidata.\n\n\n"
    text += "1.1.3 Subgrafo 3, Team Stats graph\n"
    text += "1.1.3.1 Entidades del grafo\n"
    text += "- Game: Representa un partido de fútbol específico e individualizado.\n"
    text += "- GameStats: Entidad intermedia que almacena el rendimiento estadístico técnico y disciplinario de un equipo concreto dentro de un partido específico (diferenciando si actuó como local o visitante).\n"
    text += "- TeamSeason: Representa la instancia temporal del equipo de fútbol para esa temporada específica. Se conecta directamente con el nodo correspondiente del Subgrafo 1.\n"
    text += "- Season: Entidad cronológica global que identifica la temporada o año en el que se disputa el encuentro.\n\n"
    text += "1.1.3.2 Relaciones entre entidades\n"
    text += "- playGame (TeamSeason -> Game): Conecta a la instancia del equipo en una temporada con el partido específico que disputó.\n"
    text += "- season (Game -> Season): Vincula el partido con la temporada cronológica general a la que pertenece.\n"
    text += "- game (GameStats -> Game): Enlaza el bloque de estadísticas específicas con el partido al que corresponden.\n"
    text += "- team (GameStats -> TeamSeason): Asocia el bloque de rendimiento estadístico con el equipo de la temporada que generó dichos números.\n"
    text += "- hasStats (TeamSeason -> GameStats): Relación inversa que permite navegar desde el equipo de la temporada hacia los distintos registros de estadísticas que ha acumulado en sus partidos.\n\n"
    text += "1.1.3.3 Atributos de las entidades\n"
    text += "- Game -> date (String / Literal): Fecha exacta en la que se disputó el partido de fútbol.\n"
    text += "- Game -> year (Integer / Literal): Año o temporada correspondiente al calendario del encuentro.\n"
    text += "- GameStats -> goals (Integer / Literal): Cantidad de goles reales anotados por el equipo en el encuentro.\n"
    text += "- GameStats -> xGoals (Float / Literal): Goles esperados (Expected Goals), métrica de calidad de las ocasiones creadas.\n"
    text += "- GameStats -> shots (Integer / Literal): Volumen total de disparos efectuados durante el juego.\n"
    text += "- GameStats -> shotsOnTarget (Integer / Literal): Cantidad de disparos que fueron directamente a puerta.\n"
    text += "- GameStats -> deep (Integer / Literal): Pases completados en el tercio final del campo rival (ataque profundo).\n"
    text += "- GameStats -> ppda (Float / Literal): Pases permitidos por acción defensiva, mide la intensidad de la presión.\n"
    text += "- GameStats -> fouls (Integer / Literal): Número total de infracciones o faltas cometidas por el equipo.\n"
    text += "- GameStats -> corners (Integer / Literal): Cantidad de saques de esquina a favor ejecutados.\n"
    text += "- GameStats -> yellowCards (Integer / Literal): Cantidad de tarjetas amarillas recibidas por el plantel en el juego.\n"
    text += "- GameStats -> redCards (Integer / Literal): Cantidad de tarjetas rojas (expulsiones) sufridas.\n"
    text += "- GameStats -> result (String / Literal): Resultado final obtenido por el equipo en el partido.\n"
    text += "\n\n"
    text += "1.1.4 Subgrafo 4, Games graph\n"
    text += "1.1.4.1 Entidades del grafo\n"
    text += "- Game: Representa un partido de fútbol individualizado. Es el nodo central que unifica la fecha, las probabilidades de empate y los nodos de rendimiento y apuestas.\n"
    text += "- GamePerformance: Entidad intermedia que representa el rendimiento y las probabilidades estadísticas estimadas para un equipo específico (local o visitante) en dicho encuentro.\n"
    text += "- GameBet: Entidad independiente que almacena los datos de las apuestas y las cuotas fijadas para el partido por parte de una casa de apuestas en particular.\n"
    text += "- TeamSeason: Instancia temporal que representa a cada uno de los dos equipos contendientes durante esa temporada específica.\n"
    text += "- League: Representa la liga o competición a la cual pertenece y en donde se disputa el partido.\n"
    text += "- Season: Entidad cronológica global que identifica el año de la temporada del encuentro.\n\n"
    text += "1.1.4.2 Relaciones entre entidades\n"
    text += "- playGame (TeamSeason -> Game): Conecta tanto al equipo local como al visitante con el partido que disputan.\n"
    text += "- hasGame (League -> Game): Vincula la liga o competición con cada uno de los partidos que se juegan en ella.\n"
    text += "- season (Game -> Season): Enlaza el partido con su respectivo año o temporada cronológica.\n"
    text += "- game (GamePerformance -> Game): Relaciona el nodo de rendimiento estadístico de un bando con el partido correspondiente.\n"
    text += "- team (GamePerformance -> TeamSeason): Asocia el rendimiento en el partido al equipo que lo generó.\n"
    text += "- hasPerformance (TeamSeason -> GamePerformance): Relación inversa que permite consultar las fichas de rendimiento de un equipo desde su nodo de temporada.\n"
    text += "- game (GameBet -> Game): Conecta el nodo de cuotas de una casa de apuestas con el partido al que pertenece.\n"
    text += "- hasBet (Game -> GameBet): Relación inversa que une el partido con las diferentes cuotas y casas de apuestas disponibles para el mismo.\n\n"
    text += "1.1.4.3 Atributos de las entidades\n"
    text += "- Game -> date (String / Literal): Fecha exacta de celebración del encuentro.\n"
    text += "- Game -> year (Integer / Literal): Año de la temporada correspondiente al partido.\n"
    text += "- Game -> drawProbability (Float / Literal): Probabilidad estadística estimada de que el partido finalice en empate.\n"
    text += "- GamePerformance -> goals (Integer / Literal): Cantidad de goles finales anotados por el equipo (local o visitante).\n"
    text += "- GamePerformance -> probability (Float / Literal): Probabilidad estimada de victoria asignada al equipo antes del partido.\n"
    text += "- GamePerformance -> goalsHalfTime (Integer / Literal): Cantidad de goles anotados por el equipo al finalizar el primer tiempo (descanso).\n"
    text += "- GameBet -> bettingHouse (String / Literal): Nombre identificador de la casa de apuestas (ej. 'B365', 'BW', 'WH').\n"
    text += "- GameBet -> homeOdds (Float / Literal): Cuota de pago fijada para la victoria del equipo local.\n"
    text += "- GameBet -> drawOdds (Float / Literal): Cuota de pago fijada para el resultado de empate.\n"
    text += "- GameBet -> awayOdds (Float / Literal): Cuota de pago fijada para la victoria del equipo visitante.\n"
    text += "\n\n"
    text += "1.1.5 Subgrafo 5, Players graph\n"
    text += "1.1.5.1 Entidades del grafo\n"
    text += "- Player: Representa al futbolista de forma genérica e histórica. Es el nodo estático que mantiene los datos biográficos fijos del jugador.\n"
    text += "- PlayerSeason: Entidad temporal e intermedia que representa al futbolista modelado exclusivamente en una temporada o año concreto. Almacena todas sus estadísticas físicas, técnicas, económicas y de rendimiento de ese periodo.\n"
    text += "- TeamSeason: Instancia temporal que identifica al club específico para el cual juega el futbolista durante ese año.\n"
    text += "- Season: Entidad cronológica global que identifica el año de la temporada en curso.\n"
    text += "- Country: Entidad geográfica que almacena la nacionalidad de origen o nacimiento del futbolista.\n\n"
    text += "1.1.5.2 Relaciones entre entidades\n"
    text += "- hasSeason (Player -> PlayerSeason): Conecta al nodo maestro del futbolista con sus respectivas variantes de rendimiento anual.\n"
    text += "- inSeason (PlayerSeason -> Season): Enlaza la ficha temporal del jugador con la temporada global correspondiente.\n"
    text += "- born (Player -> Country): Relaciona al futbolista con su país o nacionalidad de nacimiento.\n"
    text += "- playsFor (PlayerSeason -> TeamSeason): Vincula al jugador en una temporada específica con el equipo en su respectiva temporada contractual.\n"
    text += "- hasPlayer (TeamSeason -> PlayerSeason): Relación inversa que permite conocer la plantilla o listado de jugadores pertenecientes a un club durante un año determinado.\n\n"
    text += "1.1.5.3 Atributos de las entidades\n"
    text += "- Player -> name (String / Literal): Nombre completo del futbolista.\n"
    text += "- Player -> birth_year (Integer / Literal): Año de nacimiento del jugador.\n"
    text += "- Player -> preferred_foot (String / Literal): Lateralidad o pie preferido del futbolista.\n"
    text += "- PlayerSeason -> url (String / Literal): Enlace oficial al perfil del jugador en el portal SoFifa.\n"
    text += "- PlayerSeason -> positions (String / Literal): Posiciones secundarias o demarcaciones en las que puede jugar.\n"
    text += "- PlayerSeason -> age (Integer / Literal): Edad cronológica del futbolista en dicha temporada.\n"
    text += "- PlayerSeason -> overall_rating (Integer / Literal): Valoración general de la habilidad del futbolista.\n"
    text += "- PlayerSeason -> potential (Integer / Literal): Techo o nivel potencial máximo que se proyecta que alcance el jugador.\n"
    text += "- PlayerSeason -> team_contract (String / Literal): Nombre completo o texto identificador del club contratante.\n"
    text += "- PlayerSeason -> height (Integer / Literal): Altura física del deportista.\n"
    text += "- PlayerSeason -> weight (Integer / Literal): Peso físico del deportista.\n"
    text += "- PlayerSeason -> best_overall (Integer / Literal): La valoración media óptima alcanzada en su mejor posición táctica.\n"
    text += "- PlayerSeason -> best_position (String / Literal): Demarcación táctica donde el jugador aporta el mayor rendimiento.\n"
    text += "- PlayerSeason -> growth (Integer / Literal): Margen de crecimiento o mejora restante del atributo general.\n"
    text += "- PlayerSeason -> joined (String / Literal): Fecha exacta en la que el jugador se incorporó contractualmente al club.\n"
    text += "- PlayerSeason -> loan_date_end (String / Literal): Fecha de finalización de la cesión o préstamo.\n"
    text += "- PlayerSeason -> value (Long / Literal): Valor de mercado monetario estimado del futbolista.\n"
    text += "- PlayerSeason -> wage (Long / Literal): Salario o sueldo semanal percibido por el deportista.\n"
    text += "- PlayerSeason -> release_clause (Long / Literal): Cláusula de rescisión fijada para la compra directa de los derechos del jugador.\n"
    text += "- PlayerSeason -> total_attacking (Integer / Literal): Sumatorio de las métricas tácticas del bloque de ataque.\n"
    text += "- PlayerSeason -> total_skill (Integer / Literal): Sumatorio de las métricas asignadas a la habilidad técnica y regate.\n"
    text += "- PlayerSeason -> total_movement (Integer / Literal): Sumatorio de estadísticas físicas de desplazamiento (velocidad, agilidad).\n"
    text += "- PlayerSeason -> total_goalkeeping (Integer / Literal): Sumatorio de las habilidades exclusivas de guardameta.\n"
    text += "- PlayerSeason -> total_stats (Integer / Literal): Suma agregada de todos los puntos de estadísticas de la ficha del jugador.\n"
    text += "- PlayerSeason -> base_stats (Integer / Literal): Estadísticas base y esenciales del jugador en el motor de simulación.\n"
    text += "- PlayerSeason -> weak_foot (Integer / Literal): Nivel de habilidad o estrellas asignadas al manejo de su pierna mala.\n"
    text += "- PlayerSeason -> skill_moves (Integer / Literal): Nivel de filigranas, regates o movimientos de habilidad disponibles.\n"
    text += "- PlayerSeason -> attacking_work_rate (String / Literal): Tasa o nivel de esfuerzo e implicación ofensiva.\n"
    text += "- PlayerSeason -> defensive_work_rate (String / Literal): Tasa o nivel de esfuerzo e implicación defensiva.\n"
    text += "- PlayerSeason -> international_reputation (Integer / Literal): Reputación o estatus mediático del jugador a nivel internacional.\n"
    text += "- PlayerSeason -> physical_positioning (String / Literal): Despliegue posicional físico en el campo de juego.\n"
    text += "- PlayerSeason -> club_kit_number (Integer / Literal): Dorsal o número de camiseta utilizado por el jugador en ese equipo.\n"
    text += "- PlayerSeason -> body_type (String / Literal): Biotipo o tipo de complexión física modelada para el jugador en el videojuego FIFA.\n"
    text += "- PlayerSeason -> real_face (Boolean / Literal): Indicador booleano de si el jugador cuenta con escaneo facial real en el videojuego FIFA.\n"
    text += "- PlayerSeason -> year (Integer / Literal): Año de la temporada actual a la que corresponden los registros del plantel.\n"
    text += "\n\n"
    text += "1.1.6 Subgrafo 6, Appearances graph\n"
    text += "1.1.6.1 Entidades del grafo\n"
    text += "- PlayerAppearance: Entidad intermedia que representa la participación o actuación concreta de un futbolista en un partido determinado, almacenando sus estadísticas individuales en dicho juego.\n"
    text += "- Player: Representa al futbolista de manera global e histórica, enlazándose con el nodo maestro.\n"
    text += "- Game: Representa el partido de fútbol específico en el cual ocurre la aparición.\n\n"
    text += "1.1.6.2 Relaciones entre entidades\n"
    text += "- player (PlayerAppearance -> Player): Vincula la ficha de actuación del partido con el futbolista que la ha generado.\n"
    text += "- game (PlayerAppearance -> Game): Enlaza el registro de la actuación con el partido de fútbol correspondiente.\n"
    text += "- appearsIn (Player -> PlayerAppearance): Relación inversa que permite navegar desde el perfil general de un jugador hacia todo el conjunto de sus partidos disputados.\n"
    text += "- hasPlayerAppearance (Game -> PlayerAppearance): Relación inversa que conecta un partido con los diferentes registros de actuación individuales de los futbolistas que participaron en él.\n\n"
    text += "1.1.6.3 Atributos de las entidades\n"
    text += "- PlayerAppearance -> goals (Integer / Literal): Cantidad de goles anotados por el jugador en ese partido.\n"
    text += "- PlayerAppearance -> ownGoals (Integer / Literal): Cantidad de goles anotados en propia puerta por el futbolista.\n"
    text += "- PlayerAppearance -> shots (Integer / Literal): Volumen total de disparos efectuados por el jugador durante el encuentro.\n"
    text += "- PlayerAppearance -> xGoals (Float / Literal): Goles esperados (Expected Goals) acumulados en base a sus remates individuales.\n"
    text += "- PlayerAppearance -> xGoalsChain (Float / Literal): Métrica que mide la participación del jugador en cadenas de posesión que terminaron en disparo.\n"
    text += "- PlayerAppearance -> xGoalsBuildup (Float / Literal): Contribución del futbolista en la construcción de jugadas de ataque (excluyendo disparos y pases clave).\n"
    text += "- PlayerAppearance -> assists (Integer / Literal): Número de asistencias directas de gol realizadas.\n"
    text += "- PlayerAppearance -> keyPasses (Integer / Literal): Pases clave completados que habilitaron una oportunidad clara de remate.\n"
    text += "- PlayerAppearance -> xAssists (Float / Literal): Asistencias esperadas (Expected Assists), mide la probabilidad de que sus pases acabaran en gol.\n"
    text += "- PlayerAppearance -> position (String / Literal): Demarcación o rol táctico específico que desempeñó en el campo de juego.\n"
    text += "- PlayerAppearance -> positionOrder (Integer / Literal): Orden numérico o identificador del esquema táctico de su posición.\n"
    text += "- PlayerAppearance -> yellowCard (Integer / Literal): Tarjetas amarillas recibidas por el jugador en el transcurso del partido.\n"
    text += "- PlayerAppearance -> redCard (Integer / Literal): Tarjetas rojas o expulsiones directas sufridas por el jugador.\n"
    text += "- PlayerAppearance -> time (Integer / Literal): Cantidad total de minutos jugados por el futbolista en el encuentro.\n"
    text += "\n\n"
    text += "1.1.7 Subgrafo 7, Shots graph\n"
    text += "1.1.7.1 Entidades del grafo\n"
    text += "- Shot: Entidad de tipo evento que representa una acción de tiro o remate a portería realizada durante un partido. Es el nodo central de este subgrafo.\n"
    text += "- Game: Representa el partido de fútbol específico en el que se produce el tiro, conectando esta acción con el marco macro temporal y de equipos.\n"
    text += "- Player: Representa al futbolista implicado en la acción. Puede actuar bajo dos roles semánticos distintos dentro del evento: como ejecutor del remate o como asistente.\n\n"
    text += "1.1.7.2 Relaciones entre entidades\n"
    text += "- game (Shot -> Game): Asocia de forma directa el tiro con el partido de fútbol en el que ocurrió.\n"
    text += "- hasShot (Game -> Shot): Relación inversa que permite desglosar e identificar cronológicamente todos los remates que tuvieron lugar en un encuentro.\n"
    text += "- shooter (Shot -> Player): Vincula el evento del tiro con el futbolista que realizó el disparo o remate final.\n"
    text += "- hasShot (Player -> Shot): Relación inversa que une al jugador con el histórico de todos los remates que ha intentado.\n"
    text += "- assister (Shot -> Player): Vincula el evento del tiro con el futbolista que proporcionó el pase previo o asistencia (si existiese).\n"
    text += "- assistedShot (Player -> Shot): Relación inversa que registra qué tiros fueron generados gracias a la asistencia de ese jugador específico.\n\n"
    text += "1.1.7.3 Atributos de las entidades\n"
    text += "- Shot -> minute (Integer / Literal): Minuto cronológico exacto del partido en el que se realiza el tiro.\n"
    text += "- Shot -> situation (String / Literal): Contexto o situación de juego en la que se genera el disparo.\n"
    text += "- Shot -> lastAction (String / Literal): Acción técnica inmediatamente anterior al tiro.\n"
    text += "- Shot -> shotType (String / Literal): Superficie física de contacto o tipo de remate empleado.\n"
    text += "- Shot -> shotResult (String / Literal): Desenlace de la acción de tiro.\n"
    text += "- Shot -> xGoal (Float / Literal): Probabilidad de gol esperada (Expected Goal) asignada analíticamente a ese remate individual.\n"
    text += "- Shot -> positionX (Float / Literal): Coordenada en el eje X sobre el terreno de juego desde donde se efectuó el disparo.\n"
    text += "- Shot -> positionY (Float / Literal): Coordenada en el eje Y sobre el terreno de juego desde donde se efectuó el disparo.\n"
    text += "\n\n"
    return text
