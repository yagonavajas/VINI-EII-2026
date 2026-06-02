"""
Módulo de consultas SPARQL para la aplicación VINI
Contiene todas las consultas parametrizadas y constantes
"""

# ============================================================================
# CONSULTAS PARAMETRIZADAS (para pestañas de consultas)
# ============================================================================

QUERIES_INFO = {
    "champions": {
        "name": "Ganadores de la UEFA Champions League",
        "columns": ("Año", "Equipo", "Overall", "Formación"),
        "vars": ("year", "teamName", "overall", "formation")
    },
    "eficacia": {
        "name": "Eficacia de Goles vs Expected Goals",
        "columns": ("Equipo", "Año", "Goles Promedio", "xG Promedio", "Diferencia", "Eficacia"),
        "vars": ("teamName", "year", "avgGoals", "avgxGoals", "diferencia", "eficacia")
    },
    "formaciones": {
        "name": "Análisis de Formaciones Tácticas",
        "columns": ("Formación", "Media", "Media Ataque", "Media Defensa", "Equipos"),
        "vars": ("formation", "avgOverall", "avgAttack", "avgDefense", "equiposConFOrmacion")
    },
    "rojas": {
        "name": "Partidos con más Tarjetas Rojas",
        "columns": ("Fecha", "Equipo Local", "Equipo Visitante", "Faltas totales", "Tarjetas Rojas"),
        "vars": ("date", "homeTeam", "awayTeam", "totalFouls", "totalRedCards")
    },
    "diferencias": {
        "name": "Partidos con mayor diferencia de cuotas y sorpresa en el resultado",
        "columns": ("Fecha", "Equipo Local", "Equipo Visitante", "Goles Local", "Goles Visitante", "Cuota Local", "Cuota Visitante", "Diferencia de Cuotas"),
        "vars": ("date", "homeTeam", "awayTeam", "homeGoals", "awayGoals", "whHomeOdds", "whAwayOdds", "oddsDifference")
    },

    "casaVsFuera": {
        "name": "Goles en Casa vs Fuera",
        "columns": ("Equipo", "Año", "Goles en Casa", "Goles Fuera", "Total Partidos"),
        "vars": ("teamName", "year", "goalsHome", "goalsAway", "totalGames")
    },
    "cambiosGanadores":{
        "name": "Cambios en el rendimiento de los campeones al año siguiente",
        "columns": ("Liga", "Año", "Equipo", "Media Año Campeón", "Media Año Siguiente", "Diferencia"),
        "vars": ("nombreLiga", "anio", "nombreEquipo", "mediaEquipo", "mediaAnioSiguiente", "diferenciaMedia")
    },
    "pctgApuestas": {
        "name": "Porcentaje de Aciertos por casa de Apuestas",
        "columns": ("Casa", "Apuestas", "Aciertos", "Porcentaje"),
        "vars": ("house", "total", "aciertos", "porcentaje")
    },
    "precio_goles": {
        "name": "Precio de Goles",
        "columns": ("Jugador", "Salario Anual", "Goles Totales", "Coste por Gol"),
        "vars": ("playerName", "wageYearFmt", "totalGoals", "costPerGoalFmt")
    },
    "masGoles": {
        "name": "Jugadores con más goles en un partido",
        "columns": ("Fecha", "Jugador", "Goles"),
        "vars": ("date", "playerName", "goals")
    },
    "team_urls": {
        "name": "URLs de equipos (Sofifa)",
        "columns": ("Equipo", "Temporada", "URL"),
        "vars": ("teamName", "year", "url")
    }
}

SPARQL_QUERIES = {
    "champions": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vini: <http://vini-eii.org/>

SELECT ?year ?teamName ?overall ?formation
WHERE {
  ?winner a vini:CompetitionWinner ;
          vini:competition <http://vini-eii.org/competition/6> ;
          vini:winningTeam ?team ;
          vini:season ?season .
  
  ?team vini:hasSeason ?teamSeason .
  ?teamSeason vini:inSeason ?season ;
              vini:name ?teamName ;
              vini:overall ?overall ;
              vini:formation ?formation .
  
  BIND(SUBSTR(STR(?season), STRLEN(STR(?season)) - 3) AS ?year)
}
ORDER BY ?year ?teamName""",

    "eficacia": """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX vini: <http://vini-eii.org/>

SELECT
  ?teamName
  ?year
  (ROUND(AVG(xsd:decimal(?goals)) * 100) / 100 AS ?avgGoals)
  (ROUND(AVG(xsd:decimal(?xGoals)) * 100) / 100 AS ?avgxGoals)
  (ROUND((AVG(xsd:decimal(?goals)) - AVG(xsd:decimal(?xGoals))) * 100) / 100 AS ?diferencia)
  (IF(
      AVG(xsd:decimal(?goals)) > AVG(xsd:decimal(?xGoals)),
      "Efectivo",
      "Inefectivo"
  ) AS ?eficacia)
WHERE {
  ?stats a vini:GameStats ;
         vini:goals ?goals ;
         vini:xGoals ?xGoals ;
         vini:team ?teamSeason .

  ?teamSeason vini:name ?teamName ;
              vini:year ?year .
}
GROUP BY ?teamName ?year
ORDER BY DESC(?diferencia)
LIMIT 30""",

  "formaciones": """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX vini: <http://vini-eii.org/>

SELECT
  ?formation
  (ROUND(AVG(xsd:decimal(?overall)) * 100) / 100 AS ?avgOverall)
  (ROUND(AVG(xsd:decimal(?attack)) * 100) / 100 AS ?avgAttack)
  (ROUND(AVG(xsd:decimal(?defence)) * 100) / 100 AS ?avgDefence)
  (COUNT(?ts) AS ?equiposConFormacion)
WHERE {
  ?ts a vini:TeamSeason ;
      vini:formation ?formation ;
      vini:overall ?overall ;
      vini:attack ?attack ;
      vini:defence ?defence .
}
GROUP BY ?formation
HAVING (COUNT(?ts) > 10)
ORDER BY DESC(?avgOverall)""",

    "casaVsFuera": """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX vini: <http://vini-eii.org/>

SELECT ?teamName ?year
       (SUM(IF(?location = "home", xsd:float(?goals), 0)) as ?goalsHome)
       (SUM(IF(?location = "away", xsd:float(?goals), 0)) as ?goalsAway)
       (COUNT(?stats) as ?totalGames)
WHERE {
  ?stats a vini:GameStats .
  ?stats vini:goals ?goals .
  ?stats vini:team ?teamSeason .
  ?stats vini:game ?game .
  
  ?teamSeason vini:name ?teamName .
  ?teamSeason vini:year ?year .
  
  BIND(IF(CONTAINS(STR(?stats), "_home"), "home", "away") as ?location)
}
GROUP BY ?teamName ?year
ORDER BY DESC(?goalsHome - ?goalsAway)
LIMIT 30""",

"rojas": """PREFIX vini: <http://vini-eii.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?date ?homeTeam ?awayTeam 
       (?hFouls + ?aFouls AS ?totalFouls) 
       (?hRed + ?aRed AS ?totalRedCards)   
WHERE {
  ?game rdf:type vini:Game ;
        vini:date ?date .

  BIND(IRI(CONCAT("http://vini-eii.org/gameStats/", STRAFTER(STR(?game), "http://vini-eii.org/game/"), "_home")) AS ?statsHomeURI)
  BIND(IRI(CONCAT("http://vini-eii.org/gameStats/", STRAFTER(STR(?game), "http://vini-eii.org/game/"), "_away")) AS ?statsAwayURI)

  ?statsHomeURI rdf:type vini:GameStats ;
                vini:team ?tsHome ;
                vini:fouls ?homeFouls ;
                vini:redCards ?homeRed .
  ?tsHome vini:name ?homeTeam .

  ?statsAwayURI rdf:type vini:GameStats ;
                vini:team ?tsAway ;
                vini:fouls ?awayFouls ;
                vini:redCards ?awayRed .
  ?tsAway vini:name ?awayTeam .

  BIND(xsd:integer(?homeFouls) AS ?hFouls)
  BIND(xsd:integer(?awayFouls) AS ?aFouls)
  
  BIND(xsd:integer(?homeRed) AS ?hRed)
  BIND(xsd:integer(?awayRed) AS ?aRed)
}
ORDER BY DESC(?totalRedCards)
LIMIT 30""",

"diferencias": """PREFIX vini: <http://vini-eii.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?date ?homeTeam ?awayTeam ?homeGoals ?awayGoals ?whHomeOdds ?whAwayOdds ?oddsDifference
WHERE {
  ?game rdf:type vini:Game ;
        vini:date ?date .

  BIND(IRI(CONCAT("http://vini-eii.org/gameStats/", STRAFTER(STR(?game), "http://vini-eii.org/game/"), "_home")) AS ?statsHomeURI)
  BIND(IRI(CONCAT("http://vini-eii.org/gameStats/", STRAFTER(STR(?game), "http://vini-eii.org/game/"), "_away")) AS ?statsAwayURI)

  ?statsHomeURI vini:team ?tsHome ; 
                vini:goals ?rawHomeGoals .
  ?tsHome vini:name ?homeTeam .

  ?statsAwayURI vini:team ?tsAway ; 
                vini:goals ?rawAwayGoals .
  ?tsAway vini:name ?awayTeam .

  BIND(IRI(CONCAT("http://vini-eii.org/gameBet/", STRAFTER(STR(?game), "http://vini-eii.org/game/"), "_WH")) AS ?betURI)
  ?betURI vini:homeOdds ?rawHomeOdds ; 
          vini:awayOdds ?rawAwayOdds . 
  
  BIND(xsd:integer(?rawHomeGoals) AS ?homeGoals)
  BIND(xsd:integer(?rawAwayGoals) AS ?awayGoals)
  BIND(xsd:float(?rawHomeOdds) AS ?whHomeOdds)
  BIND(xsd:float(?rawAwayOdds) AS ?whAwayOdds)

  BIND(ABS(?whHomeOdds - ?whAwayOdds) AS ?oddsDifference)

  # FILTROS: El equipo con la cuota más alta debe haber ganado el partido
  # Caso A: El visitante era el menos favorito (awayOdds > homeOdds) pero metió más goles (awayGoals > homeGoals)
  # Caso B: El local era el menos favorito (homeOdds > awayOdds) pero metió más goles (homeGoals > awayGoals)
  FILTER(
    (?whAwayOdds > ?whHomeOdds && ?awayGoals > ?homeGoals) ||
    (?whHomeOdds > ?whAwayOdds && ?homeGoals > ?awayGoals)
  )
}
ORDER BY DESC(?oddsDifference)
LIMIT 20
""",

"cambiosGanadores": """PREFIX vini: <http://vini-eii.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?nombreLiga ?anio ?nombreEquipo ?mediaEquipo ?mediaAnioSiguiente ?diferenciaMedia
WHERE {
  # 1. Obtener el equipo ganador y su liga
  ?winnerNode rdf:type vini:CompetitionWinner ;
              vini:competition ?competitionUri ;
              vini:winningTeam ?teamUri ;
              vini:season ?seasonUri .
  
  ?competitionUri vini:competitionName ?nombreLiga .
  
  # Filtrar estrictamente por las 5 grandes ligas
  FILTER (
    REGEX(?nombreLiga, "Primera|Premier League|Serie A|Bundesliga|Ligue 1", "i")
  )
  
  # Extraer ID del equipo y año actual
  BIND(REPLACE(STR(?teamUri), "http://vini-eii.org/team/", "") AS ?idEquipo)
  BIND(REPLACE(STR(?seasonUri), "http://vini-eii.org/season/", "") AS ?anioStr)
  BIND(xsd:integer(?anioStr) AS ?anio)

  # 2. Obtener la media de la temporada actual
  BIND(URI(CONCAT("http://vini-eii.org/teamSeason/", ?idEquipo, "_", ?anioStr)) AS ?teamSeasonActualUri)
  ?teamSeasonActualUri vini:name ?nombreEquipo ;
                        vini:overall ?mediaEquipo .

  # 3. Obtener la media del año siguiente de forma obligatoria (descarta 2020)
  BIND(STR(?anio + 1) AS ?anioSiguienteStr)
  BIND(URI(CONCAT("http://vini-eii.org/teamSeason/", ?idEquipo, "_", ?anioSiguienteStr)) AS ?teamSeasonSiguienteUri)
  
  ?teamSeasonSiguienteUri vini:overall ?mediaAnioSiguiente .
  
  # 4. Calcular la diferencia matemática
  # (Media Año Siguiente - Media Año Actual)
  # Un resultado positivo significa que el equipo MEJORÓ su media al año siguiente de ser campeón.
  BIND(xsd:integer(?mediaAnioSiguiente) - xsd:integer(?mediaEquipo) AS ?diferenciaMedia)
}
# Ordenar por la diferencia (por defecto de menor a mayor, añade DESC(?diferenciaMedia) si quieres ver los que más mejoraron primero)
ORDER BY DESC(?diferenciaMedia)
""",

"pctgApuestas": """PREFIX vini: <http://vini-eii.org/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

SELECT
  ?house
  (COUNT(*) AS ?total)
  (SUM(?correct) AS ?aciertos)
  (100.0 * SUM(?correct) / COUNT(*) AS ?porcentaje)
WHERE {
  {
    SELECT ?game ?homeResult
    WHERE {
      ?stats a vini:GameStats ;
             vini:game ?game ;
             vini:result ?homeResult .
      FILTER(STRENDS(STR(?stats), "_home"))
    }
  }

  ?bet a vini:GameBet ;
       vini:game ?game ;
       vini:bettingHouse ?house ;
       vini:homeOdds ?homeOdds ;
       vini:drawOdds ?drawOdds ;
       vini:awayOdds ?awayOdds .

  BIND(xsd:decimal(?homeOdds) AS ?h)
  BIND(xsd:decimal(?drawOdds) AS ?d)
  BIND(xsd:decimal(?awayOdds) AS ?a)

  # Pronostico = cuota mas baja (favorito)
  BIND(
    IF(?h <= ?d && ?h <= ?a, "HOME",
      IF(?d <= ?a, "DRAW", "AWAY")
    ) AS ?pred
  )

  BIND(
    IF(?homeResult = "W", "HOME",
      IF(?homeResult = "D", "DRAW", "AWAY")
    ) AS ?real
  )

  BIND(IF(?pred = ?real, 1, 0) AS ?correct)
}
GROUP BY ?house
ORDER BY DESC(?porcentaje)""",

    "precio_goles": r"""PREFIX vini: <http://vini-eii.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?playerName
       (CONCAT(STR(ROUND(?wageYear * 100) / 100), "€") AS ?wageYearFmt)
       (COUNT(?shot) AS ?totalGoals)
       (CONCAT(
          STR(ROUND(
              (IF(COUNT(?shot) > 0, (?wageYear / COUNT(?shot)), 0)) * 100
          ) / 100),
          "€"
       ) AS ?costPerGoalFmt)
WHERE {
  {
    SELECT ?player ?playerName (MAX(?wageParsed) AS ?wageWeek)
    WHERE {
      ?player vini:name ?playerName ;
              vini:hasSeason ?season .
      ?season vini:wage ?wageStr .

      BIND(REPLACE(STR(?wageStr), "[^0-9\\.KM]", "") AS ?wageClean)
      FILTER(STRLEN(?wageClean) > 0)

      BIND(
        IF(CONTAINS(?wageClean, "M"),
           xsd:decimal(REPLACE(?wageClean, "M", "")) * 1000000,
           IF(CONTAINS(?wageClean, "K"),
              xsd:decimal(REPLACE(?wageClean, "K", "")) * 1000,
              xsd:decimal(?wageClean)
           )
        ) AS ?wageParsed
      )
    }
    GROUP BY ?player ?playerName
    ORDER BY DESC(?wageWeek)
    LIMIT 10
  }

  OPTIONAL {
    ?shot vini:shooter ?player ;
          vini:shotResult "Goal" .
  }

  BIND(?wageWeek * 52 AS ?wageYear)
}
GROUP BY ?playerName ?wageYear
ORDER BY DESC(?wageYear)""",

"masGoles": """ PREFIX vini: <http://vini-eii.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?date ?playerName ?goals
WHERE {
  # 1. Entramos directo a la aparición del jugador y al partido
  ?pAppearance rdf:type vini:PlayerAppearance ;
               vini:player ?player ;
               vini:game ?game ;
               vini:goals ?rawGoals .

  # 2. Sacamos su nombre
  ?player vini:name ?playerName .

  # 3. Sacamos la fecha del partido
  ?game vini:date ?date .

  # 4. Convertimos a entero y filtramos para ver quién metió 2 o más goles
  BIND(xsd:integer(?rawGoals) AS ?goals)
  FILTER(?goals >= 2)
}
ORDER BY DESC(?goals)
LIMIT 20""",

    "team_urls": """PREFIX vini: <http://vini-eii.org/>

SELECT ?teamName ?year ?url
WHERE {
    ?teamSeason vini:name ?teamName ;
                vini:year ?year ;
                vini:url ?url .
}
ORDER BY ?teamName ?year"""
}

# ============================================================================
# CONSULTAS PARA CARGAR DATOS EN COMBOBOX
# ============================================================================

FETCH_TEAMS_QUERY = """PREFIX vini: <http://vini-eii.org/>

SELECT ?teamName ?year ?url
WHERE {
    ?teamSeason vini:name ?teamName ;
                vini:year ?year ;
                vini:url ?url .
}
ORDER BY ?teamName ?year"""

FETCH_PLAYERS_QUERY = """PREFIX vini: <http://vini-eii.org/>

SELECT DISTINCT ?playerName ?year ?url
WHERE {
    ?player vini:name ?playerName ;
            vini:hasSeason ?playerSeason .
    ?playerSeason vini:year ?year ;
                  vini:url ?url .
}
ORDER BY ?playerName ?year"""

# ============================================================================
# CONSULTA PARA OBTENER PLANTILLA DE UN EQUIPO
# ============================================================================

def get_squad_query(team_name, year):
    """
    Genera la consulta SPARQL para obtener la plantilla de un equipo
    
    Args:
        team_name (str): Nombre del equipo
        year (str): Año/temporada
    
    Returns:
        str: Consulta SPARQL parametrizada
    """
    return f"""PREFIX vini: <http://vini-eii.org/>

SELECT (SAMPLE(?playerName) AS ?name) ?position ?overall ?age ?potential ?value ?wage ?club_kit_number
WHERE {{
  ?teamSeason vini:name "{team_name}" ;
              vini:year "{year}" ;
              vini:hasPlayer ?playerSeason .
  
  ?player vini:hasSeason ?playerSeason ;
          vini:name ?playerName .
  
  ?playerSeason vini:positions ?position ;
                vini:overall_rating ?overall ;
                vini:age ?age ;
                vini:potential ?potential ;
                vini:value ?value ;
                vini:wage ?wage ;
                vini:club_kit_number ?club_kit_number .
}}
GROUP BY ?player ?position ?overall ?age ?potential ?value ?wage ?club_kit_number
ORDER BY DESC (?position) DESC(?overall)"""

def get_player_stats_query(player_name):
    """
    Genera la consulta SPARQL para obtener las estadísticas de un jugador
    """
    return f"""PREFIX vini: <http://vini-eii.org/>

SELECT ?year ?position ?overall_rating ?potential ?age ?value ?wage
       ?total_attacking ?total_skill ?total_movement ?total_goalkeeping ?total_stats
       ?weak_foot ?skill_moves ?international_reputation
       ?attacking_work_rate ?defensive_work_rate ?body_type ?real_face
       ?height ?weight ?best_overall ?best_position ?growth
       ?joined ?loan_date_end ?release_clause ?club_kit_number
       ?physical_positioning ?base_stats
WHERE {{
  ?player vini:name "{player_name}" ;
          vini:hasSeason ?playerSeason .
  
  ?playerSeason vini:year ?year ;
                vini:positions ?position ;
                vini:overall_rating ?overall_rating ;
                vini:potential ?potential ;
                vini:age ?age ;
                vini:value ?value ;
                vini:wage ?wage .
  
  OPTIONAL {{ ?playerSeason vini:total_attacking ?total_attacking . }}
  OPTIONAL {{ ?playerSeason vini:total_skill ?total_skill . }}
  OPTIONAL {{ ?playerSeason vini:total_movement ?total_movement . }}
  OPTIONAL {{ ?playerSeason vini:total_goalkeeping ?total_goalkeeping . }}
  OPTIONAL {{ ?playerSeason vini:total_stats ?total_stats . }}
  OPTIONAL {{ ?playerSeason vini:weak_foot ?weak_foot . }}
  OPTIONAL {{ ?playerSeason vini:skill_moves ?skill_moves . }}
  OPTIONAL {{ ?playerSeason vini:international_reputation ?international_reputation . }}
  OPTIONAL {{ ?playerSeason vini:attacking_work_rate ?attacking_work_rate . }}
  OPTIONAL {{ ?playerSeason vini:defensive_work_rate ?defensive_work_rate . }}
  OPTIONAL {{ ?playerSeason vini:body_type ?body_type . }}
  OPTIONAL {{ ?playerSeason vini:real_face ?real_face . }}
  OPTIONAL {{ ?playerSeason vini:height ?height . }}
  OPTIONAL {{ ?playerSeason vini:weight ?weight . }}
  OPTIONAL {{ ?playerSeason vini:best_overall ?best_overall . }}
  OPTIONAL {{ ?playerSeason vini:best_position ?best_position . }}
  OPTIONAL {{ ?playerSeason vini:growth ?growth . }}
  OPTIONAL {{ ?playerSeason vini:joined ?joined . }}
  OPTIONAL {{ ?playerSeason vini:loan_date_end ?loan_date_end . }}
  OPTIONAL {{ ?playerSeason vini:release_clause ?release_clause . }}
  OPTIONAL {{ ?playerSeason vini:club_kit_number ?club_kit_number . }}
  OPTIONAL {{ ?playerSeason vini:physical_positioning ?physical_positioning . }}
  OPTIONAL {{ ?playerSeason vini:base_stats ?base_stats . }}
}}
ORDER BY DESC(?year)"""
