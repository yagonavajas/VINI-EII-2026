import pandas as pd
import numpy as np

BASE_PATH = "./Aplicacion/Fuentes/kaggle/football-database/"
OUTPUT_PATH = "./Aplicacion/Fuentes/kaggle/football-database/generados/"


def procesarTemporada(ano_inicial, ano_final):
    """
    Filtra games.csv y appearances.csv para la temporada especificada.
    Crea archivos con sufijo _X_Y_fbdb.csv donde X y Y son años.
    """
    print(f"\n{'='*60}")
    print(f"Procesando temporada {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    # Convertir años a seasons (2016/17 tiene season=2016 en BD, pero pasamos año inicial como 2016)
    season_inicial = ano_inicial - 1
    season_final = ano_final - 1
    
    GAMES_FILE = f"{BASE_PATH}games.csv"
    APPEARANCES_FILE = f"{BASE_PATH}appearances.csv"
    DELETE_FILE = f"{OUTPUT_PATH}delete_16_20.csv"
    GAMES_OUTPUT = f"{OUTPUT_PATH}games_16_20_fbdb.csv"
    APPEARANCES_OUTPUT = f"{OUTPUT_PATH}appearances_16_20_fbdb.csv"
    
    # 1. Cargar y filtrar temporada inicial (año a eliminiar)
    print(f"\n1. Leyendo games.csv...")
    games_df = pd.read_csv(GAMES_FILE, encoding='latin1')
    print(f"   Total de partidos: {len(games_df)}")
    
    # Identifica partidos fuera del rango
    games_fuera_rango = games_df[(games_df['season'] < season_inicial) | (games_df['season'] > season_final)][['gameID', 'season']].copy()
    print(f"   Partidos fuera de rango {ano_inicial}-{ano_final}: {len(games_fuera_rango)}")
    
    # 2. Guardar IDs fuera del rango
    print(f"\n2. Guardando delete_16_20.csv...")
    games_fuera_rango.to_csv(DELETE_FILE, index=False)
    print(f"   Archivo generado: {DELETE_FILE}")
    
    # 3. Crear games filtrado
    print(f"\n3. Generando games_16_20_fbdb.csv...")
    games_filtrado = games_df[(games_df['season'] >= season_inicial) & (games_df['season'] <= season_final)]
    games_filtrado.to_csv(GAMES_OUTPUT, index=False)
    print(f"   Partidos guardados: {len(games_filtrado)}")
    
    # 4. Filtrar appearances
    print(f"\n4. Procesando appearances.csv...")
    appearances_df = pd.read_csv(APPEARANCES_FILE, encoding='latin1')
    print(f"   Total appearances: {len(appearances_df)}")
    
    games_to_delete = set(games_fuera_rango['gameID'].values)
    appearances_filtrado = appearances_df[~appearances_df['gameID'].isin(games_to_delete)]
    appearances_filtrado.to_csv(APPEARANCES_OUTPUT, index=False)
    print(f"   Appearances eliminadas: {len(appearances_df) - len(appearances_filtrado)}")
    print(f"   Appearances guardadas: {len(appearances_filtrado)}")
    

def procesarEquiposTemporada(ano_inicial, ano_final):
    """
    Filtra teamstats.csv eliminando registros fuera del rango de temporadas.
    """
    print(f"\n{'='*60}")
    print(f"Procesando equipos temporada {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    # Convertir años a seasons
    season_inicial = ano_inicial - 1
    season_final = ano_final - 1
    
    TEAMSTATS_FILE = f"{BASE_PATH}teamstats.csv"
    DELETE_TEAMSTATS_FILE = f"{OUTPUT_PATH}delete_teamstats_16_20.csv"
    TEAMSTATS_OUTPUT = f"{OUTPUT_PATH}teamstats_16_20_fbdb.csv"
    
    # 1. Cargar y filtrar teamstats
    print(f"\n1. Leyendo teamstats.csv...")
    teamstats_df = pd.read_csv(TEAMSTATS_FILE, encoding='latin1')
    print(f"   Total teamstats: {len(teamstats_df)}")
    
    # Identificar teamstats fuera del rango
    teamstats_fuera_rango = teamstats_df[(teamstats_df['season'] < season_inicial) | (teamstats_df['season'] > season_final)]
    print(f"   Teamstats fuera de rango: {len(teamstats_fuera_rango)}")
    
    # 2. Guardar IDs fuera del rango
    print(f"\n2. Guardando delete_teamstats_16_20.csv...")
    teamstats_fuera_rango.to_csv(DELETE_TEAMSTATS_FILE, index=False)
    
    # 3. Filtrar teamstats dentro del rango
    print(f"\n3. Generando teamstats_16_20_fbdb.csv...")
    teamstats_filtrado = teamstats_df[(teamstats_df['season'] >= season_inicial) & (teamstats_df['season'] <= season_final)]
    teamstats_filtrado.to_csv(TEAMSTATS_OUTPUT, index=False)
    print(f"   Teamstats guardados: {len(teamstats_filtrado)}")
    

def validarYLimpiarJugadores(ano_inicial, ano_final):
    """
    Valida que los jugadores en appearances existan en players.csv.
    Crea players_16_20.csv solo con jugadores que aparecen en appearances.
    """
    print(f"\n{'='*60}")
    print(f"Validando y limpiando jugadores {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    APPEARANCES_FILE = f"{OUTPUT_PATH}appearances_16_20_fbdb.csv"
    PLAYERS_FILE = f"{BASE_PATH}players.csv"
    PLAYERS_OUTPUT = f"{OUTPUT_PATH}players_16_20_fbdb.csv"
    
    # 1. Cargar datos
    print(f"\n1. Cargando datos...")
    appearances_df = pd.read_csv(APPEARANCES_FILE, encoding='latin1')
    players_df = pd.read_csv(PLAYERS_FILE, encoding='latin1')
    print(f"   Appearances: {len(appearances_df)}")
    print(f"   Jugadores totales: {len(players_df)}")
    
    # 2. Extraer jugadores únicos en appearances
    print(f"\n2. Extrayendo jugadores que aparecen...")
    player_ids_en_appearances = set(appearances_df['playerID'].unique())
    print(f"   Jugadores únicos en appearances: {len(player_ids_en_appearances)}")
    
    # 3. Filtrar players que sí están en appearances
    print(f"\n3. Filtrando jugadores válidos...")
    players_validos = players_df[players_df['playerID'].isin(player_ids_en_appearances)]
    print(f"   Jugadores encontrados en players.csv: {len(players_validos)}")
    print(f"   Jugadores descartados: {len(players_df) - len(players_validos)}")
    
    # 4. Guardar
    print(f"\n4. Guardando players_16_20_fbdb.csv...")
    players_validos.to_csv(PLAYERS_OUTPUT, index=False)
    print(f"   Jugadores guardados: {len(players_validos)}")


def validarYLimpiarEquipos(ano_inicial, ano_final):
    """
    Valida que los equipos en teamstats existan en teams.csv.
    Crea teams_16_20.csv solo con equipos que aparecen en teamstats.
    """
    print(f"\n{'='*60}")
    print(f"Validando y limpiando equipos {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    TEAMSTATS_FILE = f"{OUTPUT_PATH}teamstats_16_20_fbdb.csv"
    TEAMS_FILE = f"{BASE_PATH}teams.csv"
    TEAMS_OUTPUT = f"{OUTPUT_PATH}teams_16_20_fbdb.csv"
    
    # 1. Cargar datos
    print(f"\n1. Cargando datos...")
    teamstats_df = pd.read_csv(TEAMSTATS_FILE, encoding='latin1')
    teams_df = pd.read_csv(TEAMS_FILE, encoding='latin1')
    print(f"   Teamstats: {len(teamstats_df)}")
    print(f"   Equipos totales: {len(teams_df)}")
    
    # 2. Extraer equipos únicos en teamstats
    print(f"\n2. Extrayendo equipos que aparecen...")
    team_ids_en_teamstats = set(teamstats_df['teamID'].unique())
    print(f"   Equipos únicos en teamstats: {len(team_ids_en_teamstats)}")
    
    # 3. Filtrar teams que sí están en teamstats
    print(f"\n3. Filtrando equipos válidos...")
    teams_validos = teams_df[teams_df['teamID'].isin(team_ids_en_teamstats)]
    print(f"   Equipos encontrados en teams.csv: {len(teams_validos)}")
    print(f"   Equipos descartados: {len(teams_df) - len(teams_validos)}")
    
    # 4. Guardar
    print(f"\n4. Guardando teams_16_20_fbdb.csv...")
    teams_validos.to_csv(TEAMS_OUTPUT, index=False)
    print(f"   Equipos guardados: {len(teams_validos)}")


def generarRelacionJugadoresEquipos():
    """
    Crea players_teams.csv con jugadores y equipos.
    - Primero: jugadores con >= 3 apariciones en una temporada con ese equipo
    - Luego: jugadores con < 3 apariciones, agrupados por (playerID, teamID) sin temporada:
      si suma de apariciones >= 3 en ese equipo, se incluye; si no, todos sus equipos
    """
    print(f"\n{'='*60}")
    print(f"Generando relación jugadores-equipos (versión mejorada)...")
    print(f"{'='*60}")
    
    APPEARANCES_FILE = f"{OUTPUT_PATH}appearances_16_20_fbdb.csv"
    GAMES_FILE = f"{OUTPUT_PATH}games_16_20_fbdb.csv"
    PLAYERS_FILE = f"{OUTPUT_PATH}players_16_20_fbdb.csv"
    TEAMS_FILE = f"{OUTPUT_PATH}teams_16_20_fbdb.csv"
    OUTPUT_FILE = f"{OUTPUT_PATH}players_teams_16_20.csv"
    
    # 1. Cargar datos (desde archivos filtrados)
    print(f"\n1. Cargando datos filtrados...")
    appearances_df = pd.read_csv(APPEARANCES_FILE, encoding='latin1')
    games_df = pd.read_csv(GAMES_FILE, encoding='latin1')
    players_df = pd.read_csv(PLAYERS_FILE, encoding='latin1')
    teams_df = pd.read_csv(TEAMS_FILE, encoding='latin1')
    print(f"   Appearances: {len(appearances_df)}")
    print(f"   Games: {len(games_df)}")
    print(f"   Jugadores: {len(players_df)}")
    print(f"   Equipos: {len(teams_df)}")
    
    # 2. Merge appearances con games para obtener teamID y season
    print(f"\n2. Uniendo appearances con games...")
    appearances_df = appearances_df.merge(
        games_df[['gameID', 'homeTeamID', 'awayTeamID', 'season']], 
        on='gameID', 
        how='left'
    )
    
    # 3. Determinar equipo basado en positionOrder
    print(f"\n3. Asignando teamID basado en positionOrder...")
    appearances_df['teamID'] = appearances_df.apply(
        lambda row: row['homeTeamID'] if row['positionOrder'] <= 11 else row['awayTeamID'],
        axis=1
    )
    
    # 4. Contar apariciones por (playerID, teamID, season)
    print(f"\n4. Contando apariciones por jugador-equipo-temporada...")
    player_team_season = appearances_df.groupby(['playerID', 'teamID', 'season']).size().reset_index(name='appearances')
    print(f"   Combinaciones jugador-equipo-temporada: {len(player_team_season)}")
    
    # 5. Separar jugadores con >= 3 apariciones y < 3 apariciones
    print(f"\n5. Separando por criterio de apariciones...")
    player_team_validos = player_team_season[player_team_season['appearances'] >= 3]
    player_team_invalidos = player_team_season[player_team_season['appearances'] < 3]
    print(f"   Combinaciones con >= 3 apariciones: {len(player_team_validos)}")
    print(f"   Combinaciones con < 3 apariciones: {len(player_team_invalidos)}")
    
    # 6. Procesar jugadores válidos (>= 3 apariciones en una temporada)
    print(f"\n6. Procesando jugadores con >= 3 apariciones en una temporada...")
    player_teams_validos = player_team_validos.groupby('playerID')['teamID'].unique().reset_index()
    player_teams_validos.columns = ['playerID', 'teamsIDS']
    
    # 7. Procesar jugadores inválidos: agrupar por (playerID, teamID) sin temporada
    print(f"\n7. Procesando jugadores con < 3 apariciones...")
    player_ids_inval_totales = set(player_team_invalidos['playerID'].unique())
    # Excluir jugadores que ya están en válidos
    player_ids_validos = set(player_teams_validos['playerID'].unique())
    player_ids_inval_totales = player_ids_inval_totales - player_ids_validos
    
    # Para jugadores inválidos, sumar apariciones por (playerID, teamID) sin temporada
    player_team_total = appearances_df[appearances_df['playerID'].isin(player_ids_inval_totales)].groupby(['playerID', 'teamID']).size().reset_index(name='appearances')
    
    # Separar en dos grupos: >= 3 apariciones totales con equipo, y < 3
    player_team_inval_3plus = player_team_total[player_team_total['appearances'] >= 3]
    player_team_inval_menos3 = player_team_total[player_team_total['appearances'] < 3]
    
    # Agrupar en dos dataframes
    if len(player_team_inval_3plus) > 0:
        player_teams_inval_3plus = player_team_inval_3plus.groupby('playerID')['teamID'].unique().reset_index()
        player_teams_inval_3plus.columns = ['playerID', 'teamsIDS']
        print(f"   Jugadores con >= 3 apariciones totales (múltiples temporadas): {len(player_teams_inval_3plus)}")
    else:
        player_teams_inval_3plus = pd.DataFrame(columns=['playerID', 'teamsIDS'])
    
    if len(player_team_inval_menos3) > 0:
        player_teams_inval_menos3 = appearances_df[appearances_df['playerID'].isin(player_team_inval_menos3['playerID'].unique())].groupby('playerID')['teamID'].unique().reset_index()
        player_teams_inval_menos3.columns = ['playerID', 'teamsIDS']
        print(f"   Jugadores con < 3 apariciones totales (todos los equipos): {len(player_teams_inval_menos3)}")
    else:
        player_teams_inval_menos3 = pd.DataFrame(columns=['playerID', 'teamsIDS'])
    
    # 8. Crear mapeo team_id -> team_name
    print(f"\n8. Creando mapeos de equipos...")
    team_id_to_name = dict(zip(teams_df['teamID'], teams_df['name']))
    
    # 9. Mapear nombres
    player_teams_validos['teamsNames'] = player_teams_validos['teamsIDS'].apply(
        lambda teams: [team_id_to_name.get(tid, '') for tid in teams]
    )
    player_teams_inval_3plus['teamsNames'] = player_teams_inval_3plus['teamsIDS'].apply(
        lambda teams: [team_id_to_name.get(tid, '') for tid in teams]
    )
    player_teams_inval_menos3['teamsNames'] = player_teams_inval_menos3['teamsIDS'].apply(
        lambda teams: [team_id_to_name.get(tid, '') for tid in teams]
    )
    
    # 10. Convertir listas a strings separados por pipe
    for df in [player_teams_validos, player_teams_inval_3plus, player_teams_inval_menos3]:
        df['teamsIDS'] = df['teamsIDS'].apply(lambda x: '|'.join(map(str, x)))
        df['teamsNames'] = df['teamsNames'].apply(lambda x: '|'.join(x))
    
    # 11. Obtener nombres de jugadores
    print(f"\n9. Agregando nombres de jugadores...")
    player_name_map = dict(zip(players_df['playerID'], players_df['name']))
    for df in [player_teams_validos, player_teams_inval_3plus, player_teams_inval_menos3]:
        df['playerName'] = df['playerID'].map(player_name_map)
    
    # 12. Reordenar columnas en orden correcto
    player_teams_validos = player_teams_validos[['playerID', 'playerName', 'teamsIDS', 'teamsNames']]
    player_teams_inval_3plus = player_teams_inval_3plus[['playerID', 'playerName', 'teamsIDS', 'teamsNames']]
    player_teams_inval_menos3 = player_teams_inval_menos3[['playerID', 'playerName', 'teamsIDS', 'teamsNames']]
    
    # 13. Concatenar todos
    print(f"\n10. Concatenando resultados...")
    player_teams = pd.concat([player_teams_validos, player_teams_inval_3plus, player_teams_inval_menos3], ignore_index=True)
    
    # 14. Guardar
    print(f"\n11. Guardando players_teams_16_20.csv...")
    player_teams.to_csv(OUTPUT_FILE, index=False)
    print(f"   Jugadores >= 3 apar./temporada: {len(player_teams_validos)}")
    print(f"   Jugadores >= 3 apar./equipo (múlt. temp.): {len(player_teams_inval_3plus)}")
    print(f"   Jugadores < 3 apariciones: {len(player_teams_inval_menos3)}")
    print(f"   Total jugadores: {len(player_teams)}")
    print(f"   Archivo generado: {OUTPUT_FILE}")



def main():
    """Ejecuta los procesamientos principales."""
    import os
    
    ano_inicial = 2016
    ano_final = 2020
    
    # Crear carpeta de salida si no existe
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Procesar temporadas de games/appearances
    procesarTemporada(ano_inicial, ano_final)
    
    # Procesar equipos (solo teamstats)
    procesarEquiposTemporada(ano_inicial, ano_final)
    
    # Validar y limpiar jugadores
    validarYLimpiarJugadores(ano_inicial, ano_final)
    
    # Validar y limpiar equipos
    validarYLimpiarEquipos(ano_inicial, ano_final)
    
    # Generar relación jugadores-equipos
    generarRelacionJugadoresEquipos()
    
    print(f"\n{'='*60}")
    print(" Todos los procesamientos completados exitosamente")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
