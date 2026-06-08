import sys
import os
from pathlib import Path
import pandas as pd

# 1. Configuración dinámica y automática del PATH de búsqueda del proyecto
# Detecta la carpeta donde reside este script de pruebas (ej: /Proyecto/Pruebas)
CURRENT_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# Sube un nivel para encontrar la raíz del proyecto (ej: /Proyecto)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_TEST_DIR, ".."))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Imports de los módulos del proyecto
from Grafo.UnificacionEntidades.Jugadores.players_id_unifier import (
    detectar_encoding, extract_initial, extract_lastname, 
    build_team_equivalences, build_fbdb_player_teams_mapping
)
# Se renombran los imports duplicados para evitar conflictos de colisión de nombres
from Grafo.UnificacionEntidades.Jugadores.players_id_unifier import normalize_text as normalize_player_text
from Grafo.UnificacionEntidades.Jugadores.players_id_unifier import _calculate_similarity_score as _calc_player_sim
from Grafo.UnificacionEntidades.Jugadores.players_id_unifier import unify_entities as unify_players

from Grafo.UnificacionEntidades.Equipos.teams_id_unifier import normalize_text as normalize_team_text
from Grafo.UnificacionEntidades.Equipos.teams_id_unifier import _calculate_similarity_score as _calc_team_sim
from Grafo.UnificacionEntidades.Equipos.teams_id_unifier import unify_entities as unify_teams
from Grafo.UnificacionEntidades.Paises.unificacionPaises import unificar_paises


# ==============================================================================
# PRUEBAS DEL MÓDULO DE EQUIPOS
# ==============================================================================

def test_normalize_text():
    assert normalize_team_text("FC Barcelona") == "baelona"
    assert normalize_team_text("Real Madrid CF") == "realmadrid"
    assert normalize_team_text("Club Atlético de Madrid (CAF)") == "clubatleticodemadridcaf"


def test_calculate_similarity_score():
    score = _calc_team_sim("fcbarranquilla", "fcbarcelona")
    assert isinstance(score, float)
    assert 0 <= score <= 100

    score = _calc_team_sim("realmadridcf", "realmadridspain")
    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_team_id_unifier():
    sofifa_df = pd.DataFrame({
        'name': ['FC Barcelona', 'Real Madrid'],
        'id': [1, 2]
    })
    fbdb_df = pd.DataFrame({
        'name': ['Barcelona FC', 'Madrid Real'],
        'teamID': [3, 4]
    })
    wikidata_df = pd.DataFrame({
        'teamLabel': ['FC Barcelona', 'Real Madrid'],
        'team': [101, 102]
    })

    # Construcción de rutas absolutas dinámicas para las salidas de equipos
    archivos_prueba_dir = os.path.join(CURRENT_TEST_DIR, 'ArchivosPrueba')
    os.makedirs(archivos_prueba_dir, exist_ok=True) # Asegura la existencia física de la carpeta
    
    output_definite_path = os.path.join(archivos_prueba_dir, 'output_definite.csv')
    output_candidates_path = os.path.join(archivos_prueba_dir, 'output_candidates.csv')

    # Ejecución utilizando la función del módulo de equipos
    definite_matches, candidate_matches, total_entities = unify_teams(
        sofifa_df, fbdb_df, 'name', 'name', 'id', 'teamID',
        threshold=50, threshold_candidates=40,
        output_file=output_definite_path,
        output_file_candidates=output_candidates_path,
        wikidata_df=wikidata_df
    )

    assert len(definite_matches) == 2
    assert len(candidate_matches) == 0
    assert total_entities == 2
    assert os.path.exists(output_definite_path)

    output_definite_df = pd.read_csv(output_definite_path)
    expected_definite_df = pd.DataFrame({
        'nombreSofifa': ['FC Barcelona', 'Real Madrid'],
        'nombrefbdb': ['Barcelona FC', 'Madrid Real'],
        'nombreWikidata': ['FC Barcelona', 'Real Madrid'],
        'idSofifa': [1, 2],
        'idfbdb': [3, 4],
        'idWikidata': [101, 102],
        'idFinal': [1, 2]
    })

    pd.testing.assert_frame_equal(output_definite_df, expected_definite_df)


# ==============================================================================
# PRUEBAS DEL MÓDULO DE JUGADORES
# ==============================================================================

def test_extract_initial():
    assert extract_initial("L. Messi") == "L"
    assert extract_initial("Cristiano Ronaldo") == "C"
    assert extract_initial("Neymar") == "N"
    assert extract_initial("") == ""


def test_extract_lastname():
    assert extract_lastname("L. Messi") == "Messi"
    assert extract_lastname("Cristiano Ronaldo") == "Ronaldo"
    assert extract_lastname("Neymar") == "Neymar"
    assert extract_lastname("") == ""


def test_normalize_player_text():
    assert normalize_player_text("L. Messi") == "lmessi"
    assert normalize_player_text("Cristiano Ronaldo") == "cristianoronaldo"
    assert normalize_player_text("Neymar") == "neymar"
    assert normalize_player_text("") == ""


def test_calculate_player_similarity_score():
    assert abs(_calc_player_sim('l messi', 'cristiano ronaldo') - 52) < 100
    assert abs(_calc_player_sim('neymar', 'neymar') - 100) < 100
    assert abs(_calc_player_sim('pele', 'pelé') - 83) < 100


def test_build_fbdb_player_teams_mapping():
    temp_file = os.path.join(CURRENT_TEST_DIR, "temp_player_teams_mapping.csv")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("playerID,teamsIDS\n1,|\n2,|")
    
    player_teams = build_fbdb_player_teams_mapping(temp_file)
    assert player_teams == {}
    os.remove(temp_file)


def test_build_team_equivalences():
    temp_file = os.path.join(CURRENT_TEST_DIR, "temp_team_equivalences.csv")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("nombreSofifa,idfbdb\nl messi,1\ncristiano ronaldo,2")
    
    team_name_to_fbdb_id = build_team_equivalences(temp_file)
    assert team_name_to_fbdb_id == {'l messi': 1, 'cristiano ronaldo': 2}
    os.remove(temp_file)


def test_player_id_unifier():
    sofifa_data = {
        'name': ['L. Messi', 'Cristiano Ronaldo', 'Neymar', 'Unknown Player'],
        'id': [1, 2, 3, 4],
        'team_contract': ['FC Barcelona', 'Real Madrid', 'Paris Saint-Germain', 'Some Team']
    }
    fbdb_data = {
        'name': ['Lionel Messi', 'Cristiano Ronaldo dos Santos Aveiro', 'Neymar Jr', 'Other'],
        'id': [101, 102, 103, 104]
    }
    sofifa_df = pd.DataFrame(sofifa_data)
    fbdb_df = pd.DataFrame(fbdb_data)

    team_name_to_fbdb_id = {
        'fc barcelona': 201,
        'real madrid': 202,
        'paris saint-germain': 203
    }

    fbdb_player_teams = {
        101: [201],
        102: [202],
        103: [203],
        104: []     
    }

    # Output paths
    archivos_prueba_dir = os.path.join(CURRENT_TEST_DIR, 'ArchivosPrueba')
    os.makedirs(archivos_prueba_dir, exist_ok=True)
    output_file = os.path.join(archivos_prueba_dir, 'jugadores_unificados_test.csv')
    output_candidates_file = os.path.join(archivos_prueba_dir, 'jugadores_candidatos_test.csv')

    for f in [output_file, output_candidates_file]:
        if os.path.exists(f):
            os.remove(f)

    unify_players(
        sofifa_df, fbdb_df,
        'name', 'name',
        'id', 'id',
        threshold=82,
        threshold_candidates=75,
        output_file=output_file,
        output_file_candidates=output_candidates_file,
        sofifa_team_col='team_contract',
        fbdb_id_numeric_col='id',
        team_name_to_fbdb_id=team_name_to_fbdb_id,
        fbdb_player_teams=fbdb_player_teams
    )

    # Check outputs exist and are not empty
    assert os.path.exists(output_file)
    assert os.path.exists(output_candidates_file)

    unificados_df = pd.read_csv(output_file, encoding='utf-8')
    candidatos_df = pd.read_csv(output_candidates_file, encoding='utf-8')

    assert len(unificados_df) >= 3

    assert len(unificados_df) == 4

    matched = unificados_df[unificados_df['idfbdb'] != '']
    assert len(matched) >= 3



# ==============================================================================
# PRUEBAS DEL MÓDULO DE PAÍSES
# ==============================================================================

def test_unificar_paises():
    paises_modulo_dir = os.path.join(ROOT_DIR, 'Grafo', 'UnificacionEntidades', 'Paises')
    ruta_salida_prueba = os.path.join(paises_modulo_dir, 'paises_unificados.csv')

    # Ejecuta la función del módulo externo
    unificar_paises()

    assert os.path.exists(ruta_salida_prueba), "El archivo de salida no se generó correctamente"

    df_output = pd.read_csv(ruta_salida_prueba)
    expected_rows = 148  
    assert len(df_output) == expected_rows, f"Se esperaban {expected_rows} filas, pero se obtuvieron {len(df_output)}"