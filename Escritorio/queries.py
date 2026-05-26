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
    "casaVsFuera": {
        "name": "Goles en Casa vs Fuera",
        "columns": ("Equipo", "Año", "Goles en Casa", "Goles Fuera", "Total Partidos"),
        "vars": ("teamName", "year", "goalsHome", "goalsAway", "totalGames")
    },
    "precio_goles": {
        "name": "Precio de Goles",
        "columns": ("Jugador", "Salario Anual", "Goles Totales", "Coste por Gol"),
        "vars": ("playerName", "wageYearFmt", "totalGoals", "costPerGoalFmt")
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
