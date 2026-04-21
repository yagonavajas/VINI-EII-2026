import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import Jaro, JaroWinkler, Levenshtein
from difflib import SequenceMatcher
import unicodedata
import os
import re
import chardet


def detectar_encoding(filepath):
    """
    Detecta automáticamente la codificación de un archivo.
    Retorna la codificación detectada.
    """
    with open(filepath, 'rb') as f:
        raw_data = f.read(100000)  # Leer los primeros 100KB
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        return encoding

def normalize_text(text):
    """Normaliza texto: elimina acentos, espacios, caracteres especiales y palabras clave"""
    text = str(text).lower()
    # Eliminar acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                   if unicodedata.category(c) != 'Mn')
    # Eliminar espacios y caracteres especiales
    text = ''.join(c for c in text if c.isalnum())
    return text

def _calculate_similarity_score(norm1, norm2):
    """
    Calcula similitud promediada con múltiples métodos complementarios:
    - Token-based (maneja palabras desordenadas)
    - String-based (maneja caracteres individuales)
    - Edit distance (Jaro, Jaro-Winkler, Levenshtein)
    - Sequence matching (diflib)
    """
    scores = []
    
    # 1. Token-based metrics (buenas para nombres con palabras reordenadas)
    scores.append(fuzz.token_set_ratio(norm1, norm2))           # Ignora orden de palabras
    scores.append(fuzz.token_sort_ratio(norm1, norm2))          # Ordena palabras y compara
    
    # 2. String-based metrics (buenas para diferencias de caracteres)
    scores.append(fuzz.ratio(norm1, norm2))                     # Similitud básica
    scores.append(fuzz.partial_ratio(norm1, norm2) * 0.9)       # Substring matching (penalizado)
    
    # 3. Edit distance metrics (buenas para typos y variaciones)
    try:
        jaro_score = Jaro.similarity(norm1, norm2) * 100        # Jaro: sensible a transposiciones
        scores.append(jaro_score)
    except:
        scores.append(0)
    
    try:
        jaro_winkler_score = JaroWinkler.similarity(norm1, norm2) * 100  # Jaro-Winkler: prefiere prefijos iguales
        scores.append(jaro_winkler_score)
    except:
        scores.append(0)
    
    try:
        levenshtein_norm = 100 * (1 - Levenshtein.normalized_distance(norm1, norm2))  # Levenshtein normalizado
        scores.append(levenshtein_norm)
    except:
        scores.append(0)
    
    # 4. Sequence matching (diferente enfoque que fuzz)
    try:
        seq_ratio = SequenceMatcher(None, norm1, norm2).ratio() * 100
        scores.append(seq_ratio)
    except:
        scores.append(0)
    
    # Retornar promedio de todas las métricas (esto da más robustez)
    return sum(scores) / len(scores)

def unify_entities(sofifa_df, fbdb_df, sofifa_name_col, fbdb_name_col, sofifa_id_col, fbdb_id_col, threshold, threshold_candidates, output_file, output_file_candidates, sofifa_team_col=None, fbdb_id_numeric_col=None, team_name_to_fbdb_id=None, fbdb_player_teams=None):
    """
    Unifica jugadores: un único match por ID de sofifa.
    Agrupa por sofifa_id, obtiene todos los equipos, busca el MEJOR match (highest score).
    """
    
    # Normalizar nombres
    sofifa_df['_norm'] = sofifa_df[sofifa_name_col].apply(normalize_text)
    fbdb_df['_norm'] = fbdb_df[fbdb_name_col].apply(normalize_text)

    if fbdb_id_numeric_col:
        fbdb_df['_fbdb_numeric_id'] = pd.to_numeric(fbdb_df[fbdb_id_numeric_col], errors='coerce')
        fbdb_df = fbdb_df[fbdb_df['_fbdb_numeric_id'].notna()].copy()
    
    # Filtrar FBDB solo a jugadores con equipo info
    if fbdb_player_teams and fbdb_id_numeric_col:
        fbdb_df = fbdb_df[fbdb_df['_fbdb_numeric_id'].astype(int).isin(fbdb_player_teams.keys())].copy()
    
    # Agrupar Sofifa por ID - obtener nombre normalizado + todos los equipos
    sofifa_groups = sofifa_df.groupby(sofifa_id_col, as_index=False).agg({
        sofifa_name_col: 'first',
        '_norm': 'first',
        sofifa_team_col if sofifa_team_col else sofifa_name_col: lambda x: list(x) if sofifa_team_col else [x.iloc[0]]
    })
    
    definite_matches = []
    candidate_matches = []
    used_fbdb_indices = set()
    used_fbdb_ids = set()
    id_final = 1
    
    total_sofifa_unique = len(sofifa_groups)
    
    for idx, sofifa_row in sofifa_groups.iterrows():
        sofifa_name = sofifa_row[sofifa_name_col]
        sofifa_norm = sofifa_row['_norm']
        sofifa_id = sofifa_row[sofifa_id_col]
        
        # Extraer TODOS los equipos del jugador (puede haber jugado en varios)
        sofifa_teams_fbdb = set()
        if sofifa_team_col and team_name_to_fbdb_id:
            team_list = sofifa_row[sofifa_team_col]
            if not isinstance(team_list, list):
                team_list = [team_list]
            
            for team_str in team_list:
                team_str = str(team_str).strip()
                if team_str and team_str.lower() != 'nan':
                    team_name = team_str.split('~')[0].strip() if '~' in team_str else team_str
                    team_name = re.sub(r'\s+\d+\s*$', '', team_name).strip()
                    team_name_lower = team_name.lower()
                    team_name_normalized = normalize_text(team_name)

                    if team_name_lower in team_name_to_fbdb_id:
                        sofifa_teams_fbdb.add(team_name_to_fbdb_id[team_name_lower])
                    else:
                        for sofifa_team_key, fbdb_id in team_name_to_fbdb_id.items():
                            if normalize_text(sofifa_team_key) == team_name_normalized:
                                sofifa_teams_fbdb.add(fbdb_id)
                                break
        
        # Filtrar FBDB disponibles
        fbdb_available = fbdb_df[~fbdb_df.index.isin(used_fbdb_indices)].copy()
        if fbdb_id_numeric_col:
            fbdb_available = fbdb_available[
                ~fbdb_available['_fbdb_numeric_id'].astype(int).isin(used_fbdb_ids)
            ].copy()
        
        # IMPORTANTE: Si sofifa tiene info de equipo pero NO encontró equivalencia en fbdb,
        # es muy probable que sean jugadores diferentes. Solo permitir match si score es PERFECTO (>=95)
        must_have_team_match = (sofifa_team_col and len(sofifa_teams_fbdb) == 0 and 
                                sofifa_row[sofifa_team_col] and 
                                str(sofifa_row[sofifa_team_col]).lower() != 'nan')
        
        # Filtrar por equipos coincidentes
        if sofifa_teams_fbdb and fbdb_player_teams and fbdb_id_numeric_col:
            fbdb_mask = fbdb_available['_fbdb_numeric_id'].astype(int).apply(
                lambda pid: any(team_id in fbdb_player_teams.get(pid, []) for team_id in sofifa_teams_fbdb)
            )
            fbdb_available = fbdb_available[fbdb_mask].copy()
        
        # Buscar mejor match
        fbdb_best_match = None
        fbdb_best_score = 0
        fbdb_best_idx = None
        
        # COMPROBACIÓN PRIORITARIA: nombre exacto + equipo coincidente = MATCH DEFINITIVO
        exact_match_found = False
        if sofifa_teams_fbdb and fbdb_player_teams and fbdb_id_numeric_col:
            for fbdb_idx, fbdb_row in fbdb_available.iterrows():
                fbdb_norm = fbdb_row['_norm']
                fbdb_player_id = int(fbdb_row['_fbdb_numeric_id'])

                # Si nombres son exactamente iguales Y el jugador fbdb juega en uno de los equipos de sofifa
                if sofifa_norm == fbdb_norm and fbdb_player_id in fbdb_player_teams:
                    fbdb_teams = fbdb_player_teams[fbdb_player_id]

                    if any(team_id in sofifa_teams_fbdb for team_id in fbdb_teams):
                        # MATCH DEFINITIVO INMEDIATO: mismo nombre + mismo equipo
                        definite_matches.append({
                            'nombreSofifa': sofifa_name,
                            'nombrefbdb': fbdb_row[fbdb_name_col],
                            'idSofifa': sofifa_id,
                            'idfbdb': fbdb_row[fbdb_id_col],
                            'idFinal': id_final
                        })
                        used_fbdb_indices.add(fbdb_idx)
                        used_fbdb_ids.add(fbdb_player_id)
                        exact_match_found = True
                        break
        
        # Si no hay match prioritario, buscar mejor match por similitud
        if not exact_match_found and len(fbdb_available) > 0:
            similitudes = fbdb_available['_norm'].apply(
                lambda x: _calculate_similarity_score(sofifa_norm, x)
            )
            fbdb_available['_score'] = similitudes.values
            fbdb_available = fbdb_available.sort_values('_score', ascending=False)
            
            fbdb_best_idx = fbdb_available.index[0]
            fbdb_best_match = fbdb_available.iloc[0]
            fbdb_best_score = fbdb_best_match['_score']
            fbdb_best_player_id = int(fbdb_best_match['_fbdb_numeric_id'])
            
            # Verificar empates
            tied_count = (fbdb_available['_score'] == fbdb_best_score).sum()
            
            # Si sofifa tiene equipo pero fbdb no encontró equivalencia,
            # solo permitir match si score es PERFECTO (>=95)
            if must_have_team_match and fbdb_best_score < 95:
                # Conservar candidatos plausibles aunque el mapeo de equipo falle,
                # para revisión manual posterior.
                if fbdb_best_score >= threshold_candidates and fbdb_best_player_id not in used_fbdb_ids:
                    candidate_matches.append({
                        'nombreSofifa': sofifa_name,
                        'nombrefbdb': fbdb_best_match[fbdb_name_col],
                        'idSofifa': sofifa_id,
                        'idfbdb': fbdb_best_match[fbdb_id_col],
                        'idFinal': id_final,
                        'similitud': round(fbdb_best_score, 2)
                    })
            elif fbdb_best_score >= threshold and tied_count == 1:
                # Match definitivo: score alto, sin empates, equipos coinciden
                definite_matches.append({
                    'nombreSofifa': sofifa_name,
                    'nombrefbdb': fbdb_best_match[fbdb_name_col],
                    'idSofifa': sofifa_id,
                    'idfbdb': fbdb_best_match[fbdb_id_col],
                    'idFinal': id_final
                })
                used_fbdb_indices.add(fbdb_best_idx)
                used_fbdb_ids.add(fbdb_best_player_id)
            elif fbdb_best_score >= threshold_candidates and fbdb_best_player_id not in used_fbdb_ids:
                # Candidato: score medio pero no definitivo
                candidate_matches.append({
                    'nombreSofifa': sofifa_name,
                    'nombrefbdb': fbdb_best_match[fbdb_name_col],
                    'idSofifa': sofifa_id,
                    'idfbdb': fbdb_best_match[fbdb_id_col],
                    'idFinal': id_final,
                    'similitud': round(fbdb_best_score, 2)
                })
        
        id_final += 1


    # Guardar resultados
    if definite_matches:
        pd.DataFrame(definite_matches).to_csv(output_file, index=False, encoding='utf-8')
    
    if candidate_matches:
        pd.DataFrame(candidate_matches).to_csv(output_file_candidates, index=False, encoding='utf-8')
    
    return definite_matches, candidate_matches, total_sofifa_unique

def build_team_equivalences(teams_file):
    """Mapeo: nombreSofifa -> idfbdb"""
    try:
        # Detectar encoding del archivo
        encoding = detectar_encoding(teams_file)
        teams_df = pd.read_csv(teams_file, encoding=encoding)
        sofifa_name_to_fbdb_id = {}
        
        for _, row in teams_df.iterrows():
            sofifa_name = str(row['nombreSofifa']).strip()
            fbdb_id = row['idfbdb']
            
            if pd.notna(sofifa_name) and pd.notna(fbdb_id):
                sofifa_name_lower = sofifa_name.lower()
                if sofifa_name_lower not in sofifa_name_to_fbdb_id:
                    sofifa_name_to_fbdb_id[sofifa_name_lower] = int(fbdb_id)
        
        return sofifa_name_to_fbdb_id
    except Exception:
        return {}

def build_fbdb_player_teams_mapping(player_teams_file):
    """Construye un diccionario de equipos para cada jugador de fbdb
    Retorna: playerID -> lista de teamsIDS (como integers)
    Detecta automáticamente la codificación del archivo.
    """
    try:
        # Detectar encoding del archivo
        encoding = detectar_encoding(player_teams_file)

        # El archivo SÍ tiene header
        teams_df = pd.read_csv(player_teams_file, encoding=encoding)

        player_teams = {}
        for _, row in teams_df.iterrows():
            try:
                player_id = int(row['playerID'])
                team_ids_str = str(row['teamsIDS'])
                team_ids = [int(tid) for tid in team_ids_str.split('|') if tid.strip().isdigit()]
                if team_ids:  # Solo agregar si hay IDs de equipos
                    player_teams[player_id] = team_ids
            except Exception:
                continue
        
        return player_teams
    except Exception:
        return {}



def player_id_unifier():
    """Unifica jugadores de sofifa y fbdb considerando equipos coincidentes"""

    base_path = os.path.dirname(os.path.abspath(__file__))
    
    sofifa_file = os.path.join(base_path, 'players_16_20_sofifa.csv')
    fbdb_file = os.path.join(base_path, 'players_16_20_fbdb.csv')
    
    sofifa_encoding = detectar_encoding(sofifa_file)
    fbdb_encoding = detectar_encoding(fbdb_file)
    
    sofifa = pd.read_csv(sofifa_file, encoding=sofifa_encoding)
    fbdb = pd.read_csv(fbdb_file, encoding=fbdb_encoding)
    
    team_equipos_path = os.path.join(base_path, '../Equipos/equipos_unificados_v2.csv')
    team_name_to_fbdb_id = build_team_equivalences(team_equipos_path)
    
    player_teams_path = os.path.join(base_path, 'players_teams_16_20_fbdb.csv')
    fbdb_player_teams = build_fbdb_player_teams_mapping(player_teams_path)
    
    unify_entities(
        sofifa, fbdb, 
        'name', 'name', 
        'id', 'playerID',
        threshold=60, 
        threshold_candidates=40,
        output_file=os.path.join(base_path, 'jugadores_unificados.csv'),
        output_file_candidates=os.path.join(base_path, 'jugadores_candidatos.csv'),
        sofifa_team_col='team_contract',
        fbdb_id_numeric_col='playerID',
        team_name_to_fbdb_id=team_name_to_fbdb_id,
        fbdb_player_teams=fbdb_player_teams
    )

if __name__ == '__main__':
    player_id_unifier()