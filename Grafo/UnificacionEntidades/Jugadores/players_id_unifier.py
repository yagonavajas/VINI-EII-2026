import pandas as pd
from rapidfuzz import fuzz
import unicodedata
import numpy as np
import os
import re

# Palabras a eliminar en la normalización
STOP_WORDS = ['fc', 'ud', 'cf', 'ac', 'ud', 'cd', 'sd', 'rc', 'be', 'aik', 'as', 'if', '1.', 'Olympique', 'Sportiva']

def normalize_text(text):
    """Normaliza texto: elimina acentos, espacios, caracteres especiales y palabras clave"""
    text = str(text).lower()
    # Eliminar acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                   if unicodedata.category(c) != 'Mn')
    # Eliminar palabras clave
    for stop_word in STOP_WORDS:
        text = text.replace(stop_word, ' ')
    # Eliminar espacios y caracteres especiales
    text = ''.join(c for c in text if c.isalnum())
    return text

def _calculate_similarity_score(norm1, norm2):
    """Calcula similitud promediada con múltiples métodos (vectorizable)"""
    scores = [
        fuzz.token_set_ratio(norm1, norm2),
        fuzz.token_sort_ratio(norm1, norm2),
        fuzz.ratio(norm1, norm2),
        fuzz.partial_ratio(norm1, norm2) * 0.8
    ]
    return sum(scores) / len(scores)

def unify_entities(sofifa_df, fbdb_df, sofifa_name_col, fbdb_name_col, sofifa_id_col, fbdb_id_col, threshold, threshold_candidates, output_file, output_file_candidates, wikidata_df=None, sofifa_team_col=None, fbdb_id_numeric_col=None, team_name_to_fbdb_id=None, fbdb_player_teams=None):
    """
    Unifica entidades con validación de equipos PRIMERO, luego similitud de tokens.
    
    Proceso:
    1. Para cada jugador Sofifa, obtiene su equipo
    2. Busca ese equipo en team_name_to_fbdb_id para obtener el idfbdb
    3. Filtra jugadores FBDB que jueguen en ese equipo (verificando player_teams)
    4. Solo entonces compara similitud de nombres
    """
    
    # Eliminar duplicados manteniendo la primera ocurrencia
    # IMPORTANTE: Filtrar por ID de sofifa (no por nombre) para evitar duplicados
    cols_to_keep = [sofifa_name_col, sofifa_id_col]
    if sofifa_team_col and sofifa_team_col in sofifa_df.columns:
        cols_to_keep.append(sofifa_team_col)
    
    # Filtrar Sofifa por ID, manteniendo solo el primero de cada ID
    sofifa_df = sofifa_df[cols_to_keep].drop_duplicates(subset=[sofifa_id_col], keep='first').reset_index(drop=True)
    # Filtrar FBDB: eliminar duplicados por nombre y verificar que tengan info en players_teams
    fbdb_df = fbdb_df[[fbdb_name_col, fbdb_id_col]].drop_duplicates(subset=[fbdb_name_col], keep='first').reset_index(drop=True)
    # Adicional: solo mantener jugadores FBDB que tengan info en fbdb_player_teams
    if fbdb_player_teams and fbdb_id_numeric_col:
        fbdb_df = fbdb_df[fbdb_df[fbdb_id_numeric_col].astype(int).isin(fbdb_player_teams.keys())].reset_index(drop=True)
    
    # Preparar wikidata (eliminar duplicados si existe)
    wikidata_prepared = None
    if wikidata_df is not None:
        wikidata_df = wikidata_df[['team', 'teamLabel']].drop_duplicates(subset=['teamLabel'], keep='first').reset_index(drop=True)
        wikidata_df['_norm'] = wikidata_df['teamLabel'].apply(normalize_text)
        wikidata_prepared = wikidata_df
    
    # Pre-normalizar todos los nombres de forma vectorizada
    sofifa_df['_norm'] = sofifa_df[sofifa_name_col].apply(normalize_text)
    fbdb_df['_norm'] = fbdb_df[fbdb_name_col].apply(normalize_text)
    
    total_entities = len(sofifa_df)
    definite_matches = []
    candidate_matches = []
    used_fbdb_indices = set()
    used_wikidata_indices = set()
    id_final = 1
    
    # Procesar por lotes para mejor rendimiento
    for sofifa_idx, sofifa_row in sofifa_df.iterrows():
        sofifa_name = sofifa_row[sofifa_name_col]
        sofifa_norm = sofifa_row['_norm']
        sofifa_id = sofifa_row[sofifa_id_col]
        
        # PASO 1: Obtener el equipo equivalente en FBDB para este jugador Sofifa
        equivalent_fbdb_team_id = None
        if sofifa_team_col and team_name_to_fbdb_id:
            # Obtener el equipo del CSV original (con toda la información)
            if sofifa_team_col in sofifa_df.columns:
                team_str = str(sofifa_df.loc[sofifa_idx, sofifa_team_col]).strip()
                if team_str and team_str.lower() != 'nan':
                    # Extraer solo el nombre del equipo (sin años)
                    # Formato: "FC Barcelona 2004 ~ 2018" -> "FC Barcelona"
                    team_name = team_str.split('~')[0].strip() if '~' in team_str else team_str
                    # Remover números al final (años)
                    team_name = re.sub(r'\s+\d+\s*$', '', team_name).strip()
                    team_name_lower = team_name.lower()
                    team_name_normalized = normalize_text(team_name)
                    
                    # Buscar en el mapeo - intentar búsqueda exacta primero
                    if team_name_lower in team_name_to_fbdb_id:
                        equivalent_fbdb_team_id = team_name_to_fbdb_id[team_name_lower]
                    else:
                        # Intentar buscar con el nombre normalizado
                        for sofifa_team_key, fbdb_id in team_name_to_fbdb_id.items():
                            if normalize_text(sofifa_team_key) == team_name_normalized:
                                equivalent_fbdb_team_id = fbdb_id
                                break
        
        # PASO 2: Filtrar jugadores FBDB que jueguen en ese equipo
        fbdb_available = fbdb_df[~fbdb_df.index.isin(used_fbdb_indices)].copy()
        
        # Si no encontramos equipo equivalente, no hacemos match (rellemamos solo con candidatos)
        fbdb_skip_if_no_team_match = False
        if sofifa_team_col and team_name_to_fbdb_id and sofifa_team_col in sofifa_df.columns:
            team_str = str(sofifa_df.loc[sofifa_idx, sofifa_team_col]).strip()
            if team_str and team_str.lower() != 'nan':
                fbdb_skip_if_no_team_match = True
        
        if equivalent_fbdb_team_id is not None and fbdb_player_teams and fbdb_id_numeric_col:
            # Filtrar por coincidencia de equipos - VECTORIZADO
            # Para cada jugador FBDB, verificar si juega en el equipo equivalente
            def has_team_in_fbdb(fbdb_player_id):
                if fbdb_player_id in fbdb_player_teams:
                    return equivalent_fbdb_team_id in fbdb_player_teams[fbdb_player_id]
                return False
            
            # Aplicar vectorizado
            team_mask = fbdb_available[fbdb_id_numeric_col].astype(int).apply(has_team_in_fbdb)
            fbdb_available = fbdb_available[team_mask].reset_index(drop=True)
        elif fbdb_skip_if_no_team_match and equivalent_fbdb_team_id is None:
            # Si había equipo en sofifa pero no encontramos equivalencia, no hacemos match definitivo
            fbdb_available = pd.DataFrame()
        
        # PASO 3: Comparar similitud de nombres solo si hay candidatos
        fbdb_best_match = None
        fbdb_best_score = 0
        fbdb_best_idx = None
        tied_count = 0
        
        if len(fbdb_available) > 0:
            similitudes = fbdb_available['_norm'].apply(
                lambda x: _calculate_similarity_score(sofifa_norm, x)
            )
            fbdb_available['_score'] = similitudes.values
            fbdb_available = fbdb_available.sort_values('_score', ascending=False)
            
            fbdb_best_idx = fbdb_available.index[0]
            fbdb_best_match = fbdb_available.iloc[0]
            fbdb_best_score = fbdb_best_match['_score']
            
            # Detectar empates en FBDB
            tied_mask = fbdb_available['_score'] == fbdb_best_score
            tied_count = tied_mask.sum()
        
        # BÚSQUEDA EN WIKIDATA
        wikidata_best_match = None
        wikidata_best_score = 0
        wikidata_best_idx = None
        
        if wikidata_prepared is not None and len(wikidata_prepared) > 0:
            wikidata_available = wikidata_prepared[~wikidata_prepared.index.isin(used_wikidata_indices)].copy()
            if len(wikidata_available) > 0:
                similitudes_wiki = wikidata_available['_norm'].apply(
                    lambda x: _calculate_similarity_score(sofifa_norm, x)
                )
                wikidata_available_copy = wikidata_available.copy()
                wikidata_available_copy['_score'] = similitudes_wiki.values
                wikidata_available_copy = wikidata_available_copy.sort_values('_score', ascending=False)
                
                wikidata_best_idx = wikidata_available_copy.index[0]
                wikidata_best_match = wikidata_available_copy.iloc[0]
                wikidata_best_score = wikidata_best_match['_score']
        
        # DETERMINAR RESULTADO PARA FBDB
        # Requisito importante: debe haber encontrado equipo equivalente para ser match definitivo
        fbdb_definite = False
        if fbdb_best_idx is not None and tied_count == 1 and fbdb_best_score >= threshold and equivalent_fbdb_team_id is not None:
            fbdb_definite = True
            used_fbdb_indices.add(fbdb_best_idx)
        
        # DETERMINAR RESULTADO PARA WIKIDATA
        wikidata_selected = False
        if wikidata_best_score >= threshold_candidates:
            wikidata_selected = True
            used_wikidata_indices.add(wikidata_best_idx)
        
        # CONSTRUIR REGISTRO - SIN WIKIDATA
        if fbdb_definite and fbdb_best_match is not None:
            # Match definitivo con FBDB
            definite_matches.append({
                'nombreSofifa': sofifa_name,
                'nombrefbdb': fbdb_best_match[fbdb_name_col],
                'idSofifa': sofifa_id,
                'idfbdb': fbdb_best_match[fbdb_id_col],
                'idFinal': id_final
            })
        else:
            # Candidato o sin match
            # Solo incluir candidatos que tengan: (1) nombre FBDB encontrado y (2) similitud mínima
            if fbdb_best_match is not None and fbdb_best_score >= threshold_candidates:
                candidate_matches.append({
                    'nombreSofifa': sofifa_name,
                    'nombrefbdb': fbdb_best_match[fbdb_name_col],
                    'idSofifa': sofifa_id,
                    'idfbdb': fbdb_best_match[fbdb_id_col],
                    'idFinal': id_final,
                    'similitud': round(fbdb_best_score, 2)
                })
        
        id_final += 1
        if (sofifa_idx + 1) % 100 == 0:
            print(f"    {sofifa_idx + 1} entidades resueltas")
        
    # Guardar resultados - SIN COLUMNAS DE WIKIDATA (no se están usando)
    if definite_matches:
        result_definite = pd.DataFrame(definite_matches)
        columns_order = ['nombreSofifa', 'nombrefbdb', 'idSofifa', 'idfbdb', 'idFinal']
        result_definite = result_definite[columns_order]
        result_definite.to_csv(output_file, index=False, encoding='utf-8')
    
    if candidate_matches:
        result_candidates = pd.DataFrame(candidate_matches)
        columns_order = ['nombreSofifa', 'nombrefbdb', 'idSofifa', 'idfbdb', 'idFinal', 'similitud']
        result_candidates = result_candidates[columns_order]
        result_candidates.to_csv(output_file_candidates, index=False, encoding='utf-8')
    
    return definite_matches, candidate_matches, total_entities

def build_wikidata_team_mapping(wikidata_file):
    """Carga los datos de WikiData desde CSV"""
    try:
        wikidata_df = pd.read_csv(wikidata_file)
        return wikidata_df
    except Exception as e:
        print(f"  Advertencia: No se pudo cargar WikiData: {e}")
        return None

def build_team_equivalences(teams_file):
    """Construye un diccionario: nombreSofifa -> idfbdb
    Con esto, dado un equipo de sofifa, obtiene el ID del equipo equivalente en FBDB
    """
    try:
        teams_df = pd.read_csv(teams_file)
        # Mapeo: nombreSofifa -> idfbdb (puede haber múltiples if there are duplicates, we take the first)
        sofifa_name_to_fbdb_id = {}
        
        for _, row in teams_df.iterrows():
            sofifa_name = str(row['nombreSofifa']).strip()
            fbdb_id = row['idfbdb']
            
            if pd.notna(sofifa_name) and pd.notna(fbdb_id):
                # Normalizar el nombre de sofifa para búsqueda
                sofifa_name_lower = sofifa_name.lower()
                if sofifa_name_lower not in sofifa_name_to_fbdb_id:
                    sofifa_name_to_fbdb_id[sofifa_name_lower] = int(fbdb_id)
        
        return sofifa_name_to_fbdb_id
    except Exception as e:
        print(f"  Advertencia: No se pudo cargar equivalencias de equipos: {e}")
        return {}

def build_fbdb_player_teams_mapping(player_teams_file):
    """Construye un diccionario de equipos para cada jugador de fbdb
    Retorna: playerID -> lista de teamsIDS (como integers)
    """
    try:
        teams_df = pd.read_csv(player_teams_file)
        player_teams = {}
        for _, row in teams_df.iterrows():
            player_id = int(row['playerID'])
            team_ids_str = str(row['teamsIDS'])
            team_ids = [int(tid) for tid in team_ids_str.split('|') if tid.strip().isdigit()]
            player_teams[player_id] = team_ids
        return player_teams
    except Exception as e:
        print(f"  Advertencia: No se pudo cargar equipos de jugadores FBDB: {e}")
        return {}



def player_id_unifier():
    """Unifica jugadores de sofifa y fbdb considerando equivalencias de equipos"""
    print("Procesando jugadores...")
    
    # Cargar datos básicos - MANTENER TODAS LAS COLUMNAS NECESARIAS
    # Usar rutas relativas desde la carpeta actual del proyecto
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    sofifa = pd.read_csv(os.path.join(base_path, 'players_16_20_sofifa.csv'))
    fbdb = pd.read_csv(os.path.join(base_path, 'players_16_20_fbdb.csv'), encoding='latin-1')
    
    # Cargar equivalencias de equipos: nombreSofifa -> idfbdb
    team_equipos_path = os.path.join(base_path, '../Equipos/equipos_unificados_v2.csv')
    team_name_to_fbdb_id = build_team_equivalences(team_equipos_path)
    
    # Cargar equipos de jugadores de fbdb: playerID -> [teamsIDS]
    player_teams_path = os.path.join(base_path, 'players_teams_16_20_fbdb.csv')
    fbdb_player_teams = build_fbdb_player_teams_mapping(player_teams_path)
    
    print(f"  - Jugadores Sofifa: {len(sofifa)}")
    print(f"  - Jugadores FBDB: {len(fbdb)}")
    print(f"  - Equivalencias de equipos cargadas: {len(team_name_to_fbdb_id)}")
    print(f"  - Jugadores FBDB con info de equipos: {len(fbdb_player_teams)}")
    
    definite, candidates, total = unify_entities(
        sofifa, fbdb, 
        'name', 'name', 
        'id', 'playerID',
        threshold=55, 
        threshold_candidates=40,
        output_file=os.path.join(base_path, 'jugadores_unificados.csv'),
        output_file_candidates=os.path.join(base_path, 'jugadores_candidatos.csv'),
        sofifa_team_col='team_contract',
        fbdb_id_numeric_col='playerID',
        team_name_to_fbdb_id=team_name_to_fbdb_id,
        fbdb_player_teams=fbdb_player_teams
    )
    
    print(f"\n  Resultados:")
    print(f"  - Jugadores procesados: {total}")
    print(f"  - Matches definitivos: {len(definite)}")
    print(f"  - Candidatos para revisión: {len(candidates)}")
    print(f"  - CSV definitivos: jugadores_unificados.csv")
    print(f"  - CSV candidatos: jugadores_candidatos.csv")

if __name__ == '__main__':
    player_id_unifier()
