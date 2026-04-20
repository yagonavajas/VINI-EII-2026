import pandas as pd
from rapidfuzz import fuzz
import unicodedata
import numpy as np

# Palabras a eliminar en la normalización
STOP_WORDS = ['fc', 'ud', 'cf', 'ac', 'ud', 'cd', 'sd', 'rc', 'be', 'aik', 'as', 'if', '1.', 'Olympique', 'Sportiva', 'Football', 'Club', 'Sport']

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
        fuzz.partial_ratio(norm1, norm2) * 0.6


    ]
    return sum(scores) / len(scores)

def unify_entities(sofifa_df, fbdb_df, sofifa_name_col, fbdb_name_col, sofifa_id_col, fbdb_id_col, threshold, threshold_candidates, output_file, output_file_candidates, wikidata_df=None):
    """
    Unifica entidades (equipos o jugadores) de dos o tres fuentes usando operaciones vectorizadas.
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
    - wikidata_df: DataFrame con datos de wikidata (contiene team, teamLabel)
    """
    
    # Eliminar duplicados manteniendo la primera ocurrencia
    sofifa_df = sofifa_df[[sofifa_name_col, sofifa_id_col]].drop_duplicates(subset=[sofifa_name_col], keep='first').reset_index(drop=True)
    fbdb_df = fbdb_df[[fbdb_name_col, fbdb_id_col]].drop_duplicates(subset=[fbdb_name_col], keep='first').reset_index(drop=True)
    
    # Preparar wikidata (eliminar duplicados si existe)
    wikidata_prepared = None
    if wikidata_df is not None:
        wikidata_df = wikidata_df[['team', 'teamLabel']].drop_duplicates(subset=['teamLabel'], keep='first').reset_index(drop=True)
        wikidata_df['_norm'] = wikidata_df['teamLabel'].apply(normalize_text)
        wikidata_prepared = wikidata_df
        print(f"  WikiData preparada con {len(wikidata_prepared)} equipos únicos")
    
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
        
        # BUSCAR EN FBDB
        fbdb_available = fbdb_df[~fbdb_df.index.isin(used_fbdb_indices)].copy()
        fbdb_best_match = None
        fbdb_best_score = 0
        
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
        else:
            tied_count = 0
        
        # BUSCAR EN WIKIDATA
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
        fbdb_definite = False
        if len(fbdb_available) > 0 and tied_count == 1 and fbdb_best_score >= threshold:
            fbdb_definite = True
            used_fbdb_indices.add(fbdb_best_idx)
        
        # DETERMINAR RESULTADO PARA WIKIDATA
        wikidata_selected = False
        if wikidata_best_score >= threshold_candidates:
            wikidata_selected = True
            used_wikidata_indices.add(wikidata_best_idx)
        
        # CONSTRUIR REGISTRO
        if fbdb_definite:
            # Match definitivo con FBDB
            definite_matches.append({
                'nombreSofifa': sofifa_name,
                'nombrefbdb': fbdb_best_match[fbdb_name_col],
                'nombreWikidata': wikidata_best_match['teamLabel'] if wikidata_selected else '',
                'idSofifa': sofifa_id,
                'idfbdb': fbdb_best_match[fbdb_id_col],
                'idWikidata': wikidata_best_match['team'] if wikidata_selected else '',
                'idFinal': id_final
            })
        else:
            # Candidato o sin match
            candidate_matches.append({
                'nombreSofifa': sofifa_name,
                'nombrefbdb': fbdb_best_match[fbdb_name_col] if fbdb_best_score >= threshold_candidates else '',
                'nombreWikidata': wikidata_best_match['teamLabel'] if wikidata_selected else '',
                'idSofifa': sofifa_id,
                'idfbdb': fbdb_best_match[fbdb_id_col] if fbdb_best_score >= threshold_candidates else '',
                'idWikidata': wikidata_best_match['team'] if wikidata_selected else '',
                'idFinal': id_final,
                'similitud': round(max(fbdb_best_score, wikidata_best_score), 2)
            })
        
        id_final += 1
        if (sofifa_idx + 1) % 100 == 0:
            print(f"    {sofifa_idx + 1} entidades resueltas")
        
    # Guardar resultados
    if definite_matches:
        result_definite = pd.DataFrame(definite_matches)
        # Ordenar columnas
        columns_order = ['nombreSofifa', 'nombrefbdb', 'nombreWikidata', 'idSofifa', 'idfbdb', 'idWikidata', 'idFinal']
        result_definite = result_definite[columns_order]
        result_definite.to_csv(output_file, index=False, encoding='utf-8')
    
    if candidate_matches:
        result_candidates = pd.DataFrame(candidate_matches)
        # Ordenar columnas
        columns_order = ['nombreSofifa', 'nombrefbdb', 'nombreWikidata', 'idSofifa', 'idfbdb', 'idWikidata', 'idFinal', 'similitud']
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

def team_id_unifier():
    """Unifica equipos de sofifa y fbdb, enriqueciendo con datos de WikiData"""
    print("Procesando equipos...")
    sofifa = pd.read_csv('./Aplicacion/Grafo/UnificacionEntidades/Equipos/teams_16_20_sofifa.csv')
    fbdb = pd.read_csv('./Aplicacion/Grafo/UnificacionEntidades/Equipos/teams_16_20_fbdb.csv')
    
    # Cargar datos de WikiData
    wikidata_df = build_wikidata_team_mapping('./Aplicacion/Grafo/UnificacionEntidades/Equipos/competiciones_wikidata.csv')
    
    definite, candidates, total = unify_entities(sofifa, fbdb, 'name', 'name', 'id', 'teamID', 
                                          threshold=55, threshold_candidates=40,
                                          output_file='./Aplicacion/Grafo/UnificacionEntidades/Equipos/equipos_unificados.csv',
                                          output_file_candidates='./Aplicacion/Grafo/UnificacionEntidades/Equipos/equipos_candidatos.csv',
                                          wikidata_df=wikidata_df)
    
    print(f"  Equipos únicos procesados: {total}")
    print(f"  Matches definitivos: {len(definite)}")
    print(f"  Candidatos para revisión: {len(candidates)}")
    print("  CSV definivos: equipos_unificados.csv")
    print("  CSV candidatos: equipos_candidatos.csv\n")

if __name__ == '__main__':
    team_id_unifier() 
