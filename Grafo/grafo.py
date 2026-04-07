import csv
import pandas as pd
from urllib.parse import quote
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Crear el grafo
g = Graph()

# Definir namespaces personalizados
FOOTBALL = Namespace("http://example.com/football/")

# Vincular los namespaces al grafo
g.bind("football", FOOTBALL)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)

# Obtener directorio del script
script_dir = Path(__file__).parent

# Leer los CSVs
teams_path = script_dir.parent / "Fuentes" / "csv_sofifa" / "teams_15_20.csv"
players_path = script_dir.parent / "Fuentes" / "csv_sofifa" / "players_15_20.csv"
competitions_path = script_dir.parent / "Fuentes" / "wikidataCompetitions" / "competiciones.csv"

teams_df = pd.read_csv(teams_path)
players_df = pd.read_csv(players_path)
competitions_df = pd.read_csv(competitions_path)

print(f"[*] Cargando {len(teams_df)} registros de equipos...")
print(f"[*] Cargando {len(players_df)} registros de jugadores...")
print(f"[*] Cargando {len(competitions_df)} registros de competiciones...")

# Almacenar entidades para evitar duplicados
teams_instances = {}  # team_name_year
player_instances = {}  # player_name_year
countries = {}
leagues = {}
positions = {}
competitions = {}
years = {}

# ===== PRIMERA PASADA: CREAR NODOS DE EQUIPOS =====
print("[*] Creando nodos de equipos, paises y ligas...")

for idx, row in teams_df.iterrows():
    if pd.isna(row['name']) or pd.isna(row['country']) or pd.isna(row['year']):
        continue
    
    team_name = str(row['name']).strip()
    country_name = str(row['country']).strip()
    league_name = str(row['league']).strip() if pd.notna(row['league']) else "Unknown"
    year = str(int(row['year']))
    
    # URL-encode para URIs validas
    team_enc = quote(team_name, safe='')
    country_enc = quote(country_name, safe='')
    league_enc = quote(league_name, safe='')
    
    # Crear nodo de PAIS (unico sin año)
    if country_name not in countries:
        country_uri = URIRef(FOOTBALL[f"country_{country_enc}"])
        countries[country_name] = country_uri
        g.add((country_uri, RDF.type, FOOTBALL.Country))
        g.add((country_uri, RDFS.label, Literal(country_name)))
    
    # Crear nodo de LIGA (unico sin año)
    league_key = f"{league_name}_{country_name}"
    if league_key not in leagues:
        league_uri = URIRef(FOOTBALL[f"league_{league_enc}_{country_enc}"])
        leagues[league_key] = league_uri
        g.add((league_uri, RDF.type, FOOTBALL.League))
        g.add((league_uri, RDFS.label, Literal(league_name)))
        g.add((league_uri, FOOTBALL.inCountry, countries[country_name]))
    
    # Crear nodo de EQUIPO ESPECIFICO (con año para evitar duplicados)
    team_instance_key = f"{team_name}_{year}"
    if team_instance_key not in teams_instances:
        team_uri = URIRef(FOOTBALL[f"team_{team_enc}_{year}"])
        teams_instances[team_instance_key] = team_uri
        
        # Propiedades basicas
        g.add((team_uri, RDF.type, FOOTBALL.Team))
        g.add((team_uri, RDFS.label, Literal(f"{team_name} ({year})")))
        g.add((team_uri, FOOTBALL.teamName, Literal(team_name)))
        g.add((team_uri, FOOTBALL.year, Literal(year, datatype=XSD.gYear)))
        g.add((team_uri, FOOTBALL.inCountry, countries[country_name]))
        g.add((team_uri, FOOTBALL.inLeague, leagues[league_key]))
        
        # Propiedades numericas del equipo
        numeric_props = {
            'overall': FOOTBALL.overall,
            'attack': FOOTBALL.attack,
            'midfield': FOOTBALL.midfield,
            'defence': FOOTBALL.defence,
            'transfer_budget': FOOTBALL.transferBudget,
            'club_worth': FOOTBALL.clubWorth,
            'players': FOOTBALL.players,
            'starting_xi_avg_age': FOOTBALL.startingXIAvgAge,
            'whole_team_avg_age': FOOTBALL.wholeTeamAvgAge,
            'domestic_prestige': FOOTBALL.domesticPrestige,
            'international_prestige': FOOTBALL.internationalPrestige
        }
        
        for col, prop in numeric_props.items():
            if col in teams_df.columns and pd.notna(row[col]):
                try:
                    val = float(row[col]) if col not in ['players', 'domestic_prestige', 'international_prestige'] else int(row[col])
                    g.add((team_uri, prop, Literal(val, datatype=XSD.float if isinstance(val, float) else XSD.integer)))
                except:
                    pass
        
        # Propiedades textuales del equipo
        text_props = {
            'formation': FOOTBALL.formation,
            'speed': FOOTBALL.speed,
            'dribbling': FOOTBALL.dribbling,
            'passing': FOOTBALL.passing,
            'positioning': FOOTBALL.positioning,
            'crossing': FOOTBALL.crossing,
            'shooting': FOOTBALL.shooting,
            'aggression': FOOTBALL.aggression,
            'pressure': FOOTBALL.pressure,
            'team_width': FOOTBALL.teamWidth,
            'defender_line': FOOTBALL.defenderLine
        }
        
        for col, prop in text_props.items():
            if col in teams_df.columns and pd.notna(row[col]):
                g.add((team_uri, prop, Literal(str(row[col]))))

print(f"[+] Equipos creados: {len(teams_instances)}")

# ===== SEGUNDA PASADA: CREAR NODOS DE JUGADORES =====
print("[*] Creando nodos de jugadores y conectandolos con equipos...")

for idx, row in players_df.iterrows():
    if pd.isna(row['name']) or pd.isna(row['year']):
        continue
    
    player_name = str(row['name']).strip()
    year = str(int(row['year']))
    
    # Extraer el nombre del equipo de 'team_contract' (formato: "Club Name YYYY ~ YYYY")
    team_contract = str(row['team_contract']).strip() if pd.notna(row['team_contract']) else "Unknown"
    # Separar el nombre del equipo del rango de fechas
    club_name = team_contract.split('~')[0].strip() if '~' in team_contract else team_contract
    
    nationality = str(row['nationality']).strip() if pd.notna(row['nationality']) else "Unknown"
    positions_str = str(row['positions']).strip() if pd.notna(row['positions']) else "Unknown"
    
    # URL-encode
    player_enc = quote(player_name, safe='')
    nat_enc = quote(nationality, safe='')
    pos_enc = quote(positions_str, safe='')
    club_enc = quote(club_name, safe='')
    
    # Crear PAIS si no existe
    if nationality not in countries:
        country_uri = URIRef(FOOTBALL[f"country_{nat_enc}"])
        countries[nationality] = country_uri
        g.add((country_uri, RDF.type, FOOTBALL.Country))
        g.add((country_uri, RDFS.label, Literal(nationality)))
    
    # Crear POSICION si no existe
    if positions_str not in positions:
        position_uri = URIRef(FOOTBALL[f"position_{pos_enc}"])
        positions[positions_str] = position_uri
        g.add((position_uri, RDF.type, FOOTBALL.Position))
        g.add((position_uri, RDFS.label, Literal(positions_str)))
    
    # Crear JUGADOR ESPECIFICO (con año)
    player_instance_key = f"{player_name}_{year}"
    if player_instance_key not in player_instances:
        player_uri = URIRef(FOOTBALL[f"player_{player_enc}_{year}"])
        player_instances[player_instance_key] = player_uri
        
        # Propiedades basicas
        g.add((player_uri, RDF.type, FOOTBALL.Player))
        g.add((player_uri, RDFS.label, Literal(f"{player_name} ({year})")))
        g.add((player_uri, FOOTBALL.playerName, Literal(player_name)))
        g.add((player_uri, FOOTBALL.year, Literal(year, datatype=XSD.gYear)))
        g.add((player_uri, FOOTBALL.nationality, countries[nationality]))
        g.add((player_uri, FOOTBALL.playPosition, positions[positions_str]))
        
        # CONECTAR JUGADOR CON EQUIPO DEL AÑO CORRESPONDIENTE
        team_instance_key = f"{club_name}_{year}"
        if team_instance_key in teams_instances:
            team_uri = teams_instances[team_instance_key]
            g.add((player_uri, FOOTBALL.playsFor, team_uri))
        else:
            # Si no encontramos el equipo, creamos un nodo minimalista
            team_uri = URIRef(FOOTBALL[f"team_{club_enc}_{year}"])
            g.add((team_uri, RDF.type, FOOTBALL.Team))
            g.add((team_uri, RDFS.label, Literal(f"{club_name} ({year})")))
            g.add((team_uri, FOOTBALL.teamName, Literal(club_name)))
            g.add((team_uri, FOOTBALL.year, Literal(year, datatype=XSD.gYear)))
            g.add((player_uri, FOOTBALL.playsFor, team_uri))
        
        # Propiedades numericas del jugador
        numeric_props = {
            'age': FOOTBALL.age,
            'overall_rating': FOOTBALL.overallRating,
            'potential': FOOTBALL.potential,
            'height': FOOTBALL.height,
            'weight': FOOTBALL.weight,
            'value': FOOTBALL.value,
            'wage': FOOTBALL.wage
        }
        
        for col, prop in numeric_props.items():
            if col in players_df.columns and pd.notna(row[col]):
                try:
                    val = float(row[col]) if col not in ['age'] else int(row[col])
                    g.add((player_uri, prop, Literal(val, datatype=XSD.float if isinstance(val, float) else XSD.integer)))
                except:
                    pass
        
        # Propiedades textuales del jugador
        text_props = {
            'preferred_foot': FOOTBALL.preferredFoot,
            'birth_year': FOOTBALL.birthYear
        }
        
        for col, prop in text_props.items():
            if col in players_df.columns and pd.notna(row[col]):
                g.add((player_uri, prop, Literal(str(row[col]))))

print(f"[+] Jugadores creados: {len(player_instances)}")

# ===== TERCERA PASADA: CREAR NODOS DE COMPETICIONES =====
print("[*] Creando nodos de competiciones y victorias...")

# Diccionario para guardar competiciones por nombre
competitions_by_name = {}

for idx, row in competitions_df.iterrows():
    if pd.isna(row['año']) or pd.isna(row['pais']) or pd.isna(row['competicion']) or pd.isna(row['equipo']):
        continue
    
    year_comp = str(int(row['año']))
    pais = str(row['pais']).strip()
    competicion = str(row['competicion']).strip()
    equipo = str(row['equipo']).strip()
    
    # URL-encode
    pais_enc = quote(pais, safe='')
    competicion_enc = quote(competicion, safe='')
    equipo_enc = quote(equipo, safe='')
    
    # Crear PAIS si no existe
    if pais not in countries:
        country_uri = URIRef(FOOTBALL[f"country_{pais_enc}"])
        countries[pais] = country_uri
        g.add((country_uri, RDF.type, FOOTBALL.Country))
        g.add((country_uri, RDFS.label, Literal(pais)))
    
    # Crear COMPETICION si no existe
    if competicion not in competitions_by_name:
        comp_uri = URIRef(FOOTBALL[f"competition_{competicion_enc}"])
        competitions_by_name[competicion] = comp_uri
        g.add((comp_uri, RDF.type, FOOTBALL.Competition))
        g.add((comp_uri, RDFS.label, Literal(competicion)))
        g.add((comp_uri, FOOTBALL.inCountry, countries[pais]))
    
    # Crear AÑO si no existe
    if year_comp not in years:
        year_uri = URIRef(FOOTBALL[f"year_{year_comp}"])
        years[year_comp] = year_uri
        g.add((year_uri, RDF.type, FOOTBALL.Year))
        g.add((year_uri, RDFS.label, Literal(year_comp, datatype=XSD.gYear)))
    
    # Crear nodo de EQUIPO GANADOR (especifico para esta competicion-año)
    team_uri = URIRef(FOOTBALL[f"team_{equipo_enc}_{year_comp}"])
    g.add((team_uri, RDF.type, FOOTBALL.Team))
    g.add((team_uri, RDFS.label, Literal(f"{equipo} ({year_comp})")))
    g.add((team_uri, FOOTBALL.teamName, Literal(equipo)))
    g.add((team_uri, FOOTBALL.inCountry, countries[pais]))
    
    # ESTRUCTURA: Equipo -en-> Año -ganador-> Competición -enpais-> País
    g.add((team_uri, FOOTBALL.en, years[year_comp]))
    g.add((years[year_comp], FOOTBALL.ganador, competitions_by_name[competicion]))
    g.add((competitions_by_name[competicion], FOOTBALL.enpais, countries[pais]))

print(f"[+] Competiciones creadas: {len(competitions_by_name)}, Anos: {len(years)}")

# Mostrar estadísticas del grafo
total_triples = len(g)
print(f"\n[=] Estadisticas del grafo completo:")
print(f"    Total de tripletas: {total_triples}")
print(f"    Equipos (instancias): {len(teams_instances)}")
print(f"    Jugadores (instancias): {len(player_instances)}")
print(f"    Paises: {len(countries)}")
print(f"    Ligas: {len(leagues)}")
print(f"    Competiciones: {len(competitions_by_name)}")
print(f"    Anos: {len(years)}")
print(f"    Posiciones: {len(positions)}")

print(f"\n[*] Primeras 40 tripletas del grafo:")
for i, (s, p, o) in enumerate(g):
    if i < 40:
        try:
            s_label = str(s).split('/')[-1]
            p_label = str(p).split('/')[-1]
            o_label = str(o).split('/')[-1]
            # Sanitizar caracteres problemáticos para impresión
            s_label = s_label.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            p_label = p_label.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            o_label = o_label.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            print(f"    {i+1}. {s_label} --> {p_label} --> {o_label}")
        except:
            pass
    else:
        break

# Exportar a formato Turtle (.ttl)
output_path = script_dir / "grafo.ttl"
g.serialize(destination=str(output_path), format="turtle", encoding='utf-8')
print(f"\n[OK] Grafo exportado a: {output_path}")

# Mostrar una muestra del archivo TTL
print("\n[*] Contenido del archivo TTL (primeras 70 lineas):")
print("="*60)
with open(str(output_path), 'r', encoding='utf-8') as f:
    lines = f.readlines()[:70]
    for line in lines:
        print(line.rstrip())
