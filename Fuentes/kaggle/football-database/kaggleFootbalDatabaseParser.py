import pandas as pd
import numpy as np
import chardet

BASE_PATH = "./Aplicacion/Fuentes/kaggle/football-database/"
OUTPUT_PATH = "./Aplicacion/Fuentes/kaggle/football-database/generados/"


def detectar_encoding(filepath):
    """
    Detecta automáticamente la codificación de un archivo.
    Retorna la codificación detectada.
    """
    with open(filepath, 'rb') as f:
        raw_data = f.read(100000)  # Leer los primeros 100KB
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        print(f"   Codificación detectada para {filepath}: {encoding} (confianza: {result['confidence']:.2%})")
        return encoding


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
    games_df = pd.read_csv(GAMES_FILE, encoding='utf-8')
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
    appearances_df = pd.read_csv(APPEARANCES_FILE, encoding='utf-8')
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
    teamstats_df = pd.read_csv(TEAMSTATS_FILE, encoding='utf-8')
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
    Detecta automáticamente la codificación de players.csv.
    """
    print(f"\n{'='*60}")
    print(f"Validando y limpiando jugadores {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    APPEARANCES_FILE = f"{OUTPUT_PATH}appearances_16_20_fbdb.csv"
    PLAYERS_FILE = f"{BASE_PATH}players.csv"
    PLAYERS_OUTPUT = f"{OUTPUT_PATH}players_16_20_fbdb.csv"
    
    # 1. Cargar datos
    print(f"\n1. Cargando datos...")
    appearances_df = pd.read_csv(APPEARANCES_FILE)
    
    # Detectar encoding de players.csv
    print(f"\n1a. Detectando codificación de players.csv...")
    players_encoding = detectar_encoding(PLAYERS_FILE)
    players_df = pd.read_csv(PLAYERS_FILE, encoding=players_encoding)
    
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
    players_validos.to_csv(PLAYERS_OUTPUT, index=False, encoding='utf-8')
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
    teamstats_df = pd.read_csv(TEAMSTATS_FILE, encoding='utf-8')
    teams_df = pd.read_csv(TEAMS_FILE, encoding='utf-8')
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


def procesarShots(ano_inicial, ano_final):
    """
    Filtra shots.csv eliminando los disparos de partidos que están fuera del rango.
    Guarda el resultado en shots_16_20_fbdb.csv.
    """
    print(f"\n{'='*60}")
    print(f"Procesando shots {ano_inicial}/{ano_final}...")
    print(f"{'='*60}")
    
    SHOTS_FILE = f"{BASE_PATH}shots.csv"
    DELETE_FILE = f"{OUTPUT_PATH}delete_16_20.csv"
    SHOTS_OUTPUT = f"{OUTPUT_PATH}shots_16_20_fbdb.csv"
    
    # 1. Cargar datos
    print(f"\n1. Leyendo shots.csv...")
    shots_df = pd.read_csv(SHOTS_FILE, encoding='utf-8')
    print(f"   Total de disparos: {len(shots_df)}")
    
    # 2. Cargar IDs de partidos a eliminar
    print(f"\n2. Leyendo partidos a eliminar (delete_16_20.csv)...")
    delete_df = pd.read_csv(DELETE_FILE, encoding='utf-8')
    games_to_delete = set(delete_df['gameID'].values)
    print(f"   Partidos a eliminar: {len(games_to_delete)}")
    
    # 3. Filtrar shots eliminando los de partidos fuera del rango
    print(f"\n3. Filtrando shots...")
    shots_filtrado = shots_df[~shots_df['gameID'].isin(games_to_delete)]
    print(f"   Disparos eliminados: {len(shots_df) - len(shots_filtrado)}")
    print(f"   Disparos guardados: {len(shots_filtrado)}")
    
    # 4. Guardar resultado
    print(f"\n4. Guardando shots_16_20_fbdb.csv...")
    shots_filtrado.to_csv(SHOTS_OUTPUT, index=False, encoding='utf-8')
    print(f"   Archivo generado: {SHOTS_OUTPUT}")


def generarRelacionJugadoresEquipos():
    """
    Crea players_teams.csv con jugadores y equipos.
    
    Lógica CORRECTA:
    1. Para cada juego, procesar las apariciones en el orden del archivo (sin reordenar)
    2. Contar GKs acumulativamente mientras se lee el archivo
    3. Si acumulado de GKs <= 1 → equipo local (homeTeamID)
    4. Si acumulado de GKs >= 2 → equipo visitante (awayTeamID)
    5. Una sola vez por equipo (sin duplicados)
    """
    print(f"\n{'='*60}")
    print(f"Generando relación jugadores-equipos (LÓGICA CORRECTA)...")
    print(f"{'='*60}")
    
    APPEARANCES_FILE = f"{OUTPUT_PATH}appearances_16_20_fbdb.csv"
    GAMES_FILE = f"{OUTPUT_PATH}games_16_20_fbdb.csv"
    PLAYERS_FILE = f"{OUTPUT_PATH}players_16_20_fbdb.csv"
    TEAMS_FILE = f"{OUTPUT_PATH}teams_16_20_fbdb.csv"
    OUTPUT_FILE = f"{OUTPUT_PATH}players_teams_16_20.csv"
    
    # 1. Cargar datos
    print(f"\n1. Cargando datos filtrados...")
    appearances_df = pd.read_csv(APPEARANCES_FILE, dtype={'gameID': 'int64', 'playerID': 'int64'})
    games_df = pd.read_csv(GAMES_FILE, usecols=['gameID', 'homeTeamID', 'awayTeamID'], dtype={'gameID': 'int64', 'homeTeamID': 'int64', 'awayTeamID': 'int64'})
    
    # Detectar encoding de players.csv
    print(f"   Detectando codificación de players_16_20.csv...")
    players_encoding = detectar_encoding(PLAYERS_FILE)
    players_df = pd.read_csv(PLAYERS_FILE, encoding=players_encoding, dtype={'playerID': 'int64'})
    
    teams_df = pd.read_csv(TEAMS_FILE, dtype={'teamID': 'int64'})
    print(f"   Appearances: {len(appearances_df)}")
    print(f"   Games: {len(games_df)}")
    print(f"   Jugadores: {len(players_df)}")
    print(f"   Equipos: {len(teams_df)}")
    
    # 2. Crear mapeos
    print(f"\n2. Creando mapeos...")
    team_id_to_name = dict(zip(teams_df['teamID'], teams_df['name']))
    player_name_map = dict(zip(players_df['playerID'], players_df['name']))
    
    # 3. Merge: Unir appearances con games
    print(f"\n3. Uniendo appearances con games...")
    appearances_merged = appearances_df.merge(
        games_df,
        on='gameID',
        how='left'
    )
    print(f"   Merged appearances: {len(appearances_merged)}")
    
    # 4. Función para procesar cada juego
    print(f"\n4. Aplicando lógica de asignación por juego...")
    
    def assign_teams_by_game(group):
        """
        Para cada juego, asigna equipos basado en conteo acumulado de GKs.
        Procesa en el orden original del dataframe (orden del archivo).
        """
        # Contar GKs acumulativamente (cumsum)
        group['gk_cumsum'] = (group['position'] == 'GK').cumsum()
        
        # Asignar equipo:
        # - Si acumulado de GKs <= 1 → equipo local
        # - Si acumulado de GKs >= 2 → equipo visitante
        group['assigned_team'] = np.where(
            group['gk_cumsum'] <= 1,
            group['homeTeamID'],
            group['awayTeamID']
        )
        
        return group
    
    # Aplicar la lógica por groupby sin reordenar
    appearances_merged = appearances_merged.groupby('gameID', sort=False, group_keys=False).apply(
        assign_teams_by_game
    )
    
    # 5. Filtrar filas válidas y agrupar por jugador
    print(f"\n5. Agrupando equipos únicos por jugador...")
    valid_appearances = appearances_merged[['playerID', 'assigned_team']].copy()
    
    # Obtener equipos únicos por jugador
    player_teams_grouped = valid_appearances.groupby('playerID')['assigned_team'].apply(
        lambda x: sorted(list(set(x)))
    ).reset_index()
    player_teams_grouped.columns = ['playerID', 'team_ids']
    
    # Asegurar que playerID es int64
    player_teams_grouped['playerID'] = player_teams_grouped['playerID'].astype('int64')
    
    # 6. Formatear resultado
    print(f"\n6. Formateando resultado...")
    player_teams_grouped['teamsIDS'] = player_teams_grouped['team_ids'].apply(
        lambda x: '|'.join([str(int(tid)) for tid in x])
    )
    player_teams_grouped['teamsNames'] = player_teams_grouped['team_ids'].apply(
        lambda x: '|'.join([team_id_to_name.get(int(tid), '') for tid in x])
    )
    
    # 7. Agregar nombres de jugadores
    player_teams_grouped['playerName'] = player_teams_grouped['playerID'].map(player_name_map)
    
    # 8. Seleccionar columnas finales
    player_teams = player_teams_grouped[['playerID', 'playerName', 'teamsIDS', 'teamsNames']].copy()
    player_teams['playerID'] = player_teams['playerID'].astype('int64')
    
    # 9. Guardar resultado
    print(f"\n7. Guardando players_teams_16_20.csv...")
    player_teams.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"   Total jugadores procesados: {len(player_teams)}")
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
    
    # Procesar shots
    procesarShots(ano_inicial, ano_final)
    
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
