import pandas as pd
from rapidfuzz import fuzz
import unicodedata
import numpy as np

# Palabras a eliminar en la normalización
STOP_WORDS = ['fc', 'ud', 'cf', 'ac', 'ud', 'cd', 'sd', 'rc', 'be', 'aik', 'as', 'if', '1.', 'Olympique']

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

def unify_entities(sofifa_df, fbdb_df, sofifa_name_col, fbdb_name_col, sofifa_id_col, fbdb_id_col, threshold, threshold_candidates, output_file, output_file_candidates):
    """
    Unifica entidades (equipos o jugadores) de dos fuentes diferentes usando operaciones vectorizadas.
    Parámetros:
    - sofifa_df: DataFrame de sofifa
    - fbdb_df: DataFrame de fbdb
    - sofifa_name_col: nombre de columna para nombre en sofifa
    - fbdb_name_col: nombre de columna para nombre en fbdb
    - sofifa_id_col: nombre de columna para ID en sofifa
    - fbdb_id_col: nombre de columna para ID en fbdb
    - threshold: umbral de similitud para considerar un match definitivo
    - threshold_candidates: umbral para mostrar candidatos como opciones
    - output_file: ruta del archivo CSV con matches definitivos
    - output_file_candidates: ruta del archivo CSV con candidatos para revisión manual
    """
    
    # Eliminar duplicados manteniendo la primera ocurrencia
    sofifa_df = sofifa_df[[sofifa_name_col, sofifa_id_col]].drop_duplicates(subset=[sofifa_name_col], keep='first').reset_index(drop=True)
    fbdb_df = fbdb_df[[fbdb_name_col, fbdb_id_col]].drop_duplicates(subset=[fbdb_name_col], keep='first').reset_index(drop=True)
    
    # Pre-normalizar todos los nombres de forma vectorizada
    sofifa_df['_norm'] = sofifa_df[sofifa_name_col].apply(normalize_text)
    fbdb_df['_norm'] = fbdb_df[fbdb_name_col].apply(normalize_text)
    
    total_entities = len(sofifa_df)
    definite_matches = []
    candidate_matches = []
    used_fbdb_indices = set()
    id_final = 1
    
    # Procesar por lotes para mejor rendimiento
    for sofifa_idx, sofifa_row in sofifa_df.iterrows():
        sofifa_name = sofifa_row[sofifa_name_col]
        sofifa_norm = sofifa_row['_norm']
        sofifa_id = sofifa_row[sofifa_id_col]
        
        # Crear matriz de similitudes usando vectorización
        # Filtrar fbdb excluyendo ya asignados
        fbdb_available = fbdb_df[~fbdb_df.index.isin(used_fbdb_indices)].copy()
        
        if len(fbdb_available) == 0:
            # Sin candidatos disponibles
            candidate_matches.append({
                'nombreSofifa': sofifa_name,
                'nombrefbdb': '',
                'idSofifa': sofifa_id,
                'idfbdb': '',
                'idFinal': id_final,
                'similitud': 0
            })
            id_final += 1
            continue
        
        # Vectorizar cálculo de similitud para todos los disponibles
        similitudes = fbdb_available['_norm'].apply(
            lambda x: _calculate_similarity_score(sofifa_norm, x)
        )
        
        # Agregar similitudes al df y ordenar
        fbdb_available = fbdb_available.copy()
        fbdb_available['_score'] = similitudes.values
        fbdb_available = fbdb_available.sort_values('_score', ascending=False)
        
        # Obtener el mejor match
        best_idx = fbdb_available.index[0]
        best_match = fbdb_available.iloc[0]
        best_score = best_match['_score']
        
        # Detectar empates: verificar cuántas entidades tienen el mismo score máximo
        tied_mask = fbdb_available['_score'] == best_score
        tied_count = tied_mask.sum()
        
        # Si hay empate (>= 2 con el mismo score) o no supera el threshold, ir a candidatos
        if tied_count > 1 or best_score < threshold:
            # Recolectar candidatos que superen threshold_candidates
            candidates_mask = fbdb_available['_score'] >= threshold_candidates
            candidates_data = fbdb_available[candidates_mask]
            
            if len(candidates_data) > 0:
                # Una fila por candidato
                for _, cand_row in candidates_data.iterrows():
                    candidate_matches.append({
                        'nombreSofifa': sofifa_name,
                        'nombrefbdb': cand_row[fbdb_name_col],
                        'idSofifa': sofifa_id,
                        'idfbdb': cand_row[fbdb_id_col],
                        'idFinal': id_final,
                        'similitud': round(cand_row['_score'], 2)
                    })
            else:
                # Sin candidatos
                candidate_matches.append({
                    'nombreSofifa': sofifa_name,
                    'nombrefbdb': '',
                    'idSofifa': sofifa_id,
                    'idfbdb': '',
                    'idFinal': id_final,
                    'similitud': 0
                })
        else:
            # Si hay match definitivo (>= threshold sin empates)
            definite_matches.append({
                'nombreSofifa': sofifa_name,
                'nombrefbdb': best_match[fbdb_name_col],
                'idSofifa': sofifa_id,
                'idfbdb': best_match[fbdb_id_col],
                'idFinal': id_final
            })
            used_fbdb_indices.add(best_idx)
        
        id_final += 1
        if (sofifa_idx + 1) % 100 == 0:
            print(f"    {sofifa_idx + 1} entidades resueltas")
        
    # Guardar resultados
    if definite_matches:
        result_definite = pd.DataFrame(definite_matches)
        result_definite.to_csv(output_file, index=False, encoding='utf-8')
    
    if candidate_matches:
        result_candidates = pd.DataFrame(candidate_matches)
        result_candidates.to_csv(output_file_candidates, index=False, encoding='utf-8')
    
    return definite_matches, candidate_matches, total_entities

def team_id_unifier():
    """Unifica equipos de sofifa y fbdb"""
    print("Procesando equipos...")
    sofifa = pd.read_csv('./Aplicacion/Grafo/Datos/teams_16_20_sofifa.csv')
    fbdb = pd.read_csv('./Aplicacion/Grafo/Datos/teams_fbdb.csv')
    
    definite, candidates, total = unify_entities(sofifa, fbdb, 'name', 'name', 'id', 'teamID', 
                                          threshold=55, threshold_candidates=45,
                                          output_file='./Aplicacion/Grafo/Datos/equipos_unificados.csv',
                                          output_file_candidates='./Aplicacion/Grafo/Datos/equipos_candidatos.csv')
    
    print(f"  Equipos únicos procesados: {total}")
    print(f"  Matches definitivos: {len(definite)}")
    print(f"  Candidatos para revisión: {len(candidates)}")
    print("  CSV definivos: equipos_unificados.csv")
    print("  CSV candidatos: equipos_candidatos.csv\n")

def extract_player_name_from_url(url):
    """Extrae el nombre del jugador de la URL de sofifa
    Ej: https://sofifa.com/player/158023/lionel-messi/160058/ -> lionel-messi
    """
    if pd.isna(url):
        return ""
    url_str = str(url)
    parts = url_str.split('/')
    # El formato es: https://sofifa.com/player/{id}/{name}/{some_id}/
    # parts[5] debería ser el nombre
    if len(parts) >= 6:
        return parts[5]
    return ""

def player_id_unifier():
    """Unifica jugadores de sofifa y fbdb"""
    print("Procesando jugadores...")
    sofifa = pd.read_csv('./Aplicacion/Grafo/Datos/players_16_20_sofifa.csv')
    fbdb = pd.read_csv('./Aplicacion/Grafo/Datos/players_fbdb.csv', encoding='latin-1')
    
    # Extraer nombre de la URL de sofifa
    sofifa['name_from_url'] = sofifa['url'].apply(extract_player_name_from_url)
    
    definite, candidates, total = unify_entities(sofifa, fbdb, 'name_from_url', 'name', 'id', 'playerID',
                                          threshold=60, threshold_candidates=45,
                                          output_file='./Aplicacion/Grafo/Datos/jugadores_unificados.csv',
                                          output_file_candidates='./Aplicacion/Grafo/Datos/jugadores_candidatos.csv')
    
    print(f"  Jugadores únicos procesados: {total}")
    print(f"  Matches definitivos: {len(definite)}")
    print(f"  Candidatos para revisión: {len(candidates)}")
    print("  CSV definitivos: jugadores_unificados.csv")
    print("  CSV candidatos: jugadores_candidatos.csv\n")

if __name__ == '__main__':
    #team_id_unifier()
    player_id_unifier() 
