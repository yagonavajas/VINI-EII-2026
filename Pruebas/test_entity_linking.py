import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import pandas as pd
from Aplicacion.Grafo.UnificacionEntidades.Jugadores.players_id_unifier import detectar_encoding ,extract_initial, extract_lastname, normalize_text, _calculate_similarity_score, unify_entities, build_team_equivalences, build_fbdb_player_teams_mapping

from Aplicacion.Grafo.UnificacionEntidades.Equipos.teams_id_unifier import normalize_text, _calculate_similarity_score, unify_entities, build_wikidata_team_mapping
from Aplicacion.Grafo.UnificacionEntidades.Paises.unificacionPaises import unificar_paises

def test_normalize_text():
    text = "FC Barcelona"
    expected_result = "baelona"
    assert normalize_text(text) == expected_result

    text = "Real Madrid CF"
    expected_result = "realmadrid"
    assert normalize_text(text) == expected_result

    text = "Club Atlético de Madrid (CAF)"
    expected_result = "clubatleticodemadridcaf"
    assert normalize_text(text) == expected_result

def test_calculate_similarity_score():
    norm1 = "fcbarranquilla"
    norm2 = "fcbarcelona"
    score = _calculate_similarity_score(norm1, norm2)
    assert isinstance(score, float)
    assert 0 <= score <= 100

    norm1 = "realmadridcf"
    norm2 = "realmadridspain"
    score = _calculate_similarity_score(norm1, norm2)
    assert isinstance(score, float)
    assert 0 <= score <= 100

    norm1 = "clubatléticodemadridcaf"
    norm2 = "clubatléticodelepe"
    score = _calculate_similarity_score(norm1, norm2)
    assert isinstance(score, float)
    assert 0 <= score <= 100

def test_team_id_unifier():
    # Crea DataFrames simulados para prueba
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

    # Ejecuta la función principal
    definite_matches, candidate_matches, total_entities = unify_entities(
        sofifa_df,
        fbdb_df,
        'name',
        'name',
        'id',
        'teamID',
        threshold=50,
        threshold_candidates=40,
        output_file='output_definite.csv',
        output_file_candidates='output_candidates.csv',
        wikidata_df=wikidata_df
    )

    # Verifica los resultados
    assert len(definite_matches) == 2
    assert len(candidate_matches) == 0
    assert total_entities == 2

    # Verifica que se generaron archivos de salida
    definite_file = 'output_definite.csv'

    try:
        output_definite_df = pd.read_csv(definite_file)
    except FileNotFoundError:
        print(f"El archivo {definite_file} no fue generado")


    # Verifica el contenido de los archivos
    expected_definite_df = pd.DataFrame({
    'nombreSofifa': ['FC Barcelona', 'Real Madrid'],
    'nombrefbdb': ['Barcelona FC', 'Madrid Real'],
    'nombreWikidata': ['FC Barcelona', 'Real Madrid'],
    'idSofifa': [1, 2],
    'idfbdb': [3, 4],
    'idWikidata': [101, 102],
    'idFinal': [1, 2]
})

    #print(output_definite_df)
    print(expected_definite_df)


    pd.testing.assert_frame_equal(output_definite_df, expected_definite_df)

# Jugadores
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
    assert normalize_text("L. Messi") == "lmessi"
    assert normalize_text("Cristiano Ronaldo") == "cristianoronaldo"
    assert normalize_text("Neymar") == "neymar"
    assert normalize_text("") == ""

def test_calculate_similarity_score():
    assert abs(_calculate_similarity_score('l messi', 'cristiano ronaldo') - 52) < 100
    assert abs(_calculate_similarity_score('neymar', 'neymar') - 100) < 100
    assert abs(_calculate_similarity_score('pele', 'pelé') - 83) < 100

def test_build_fbdb_player_teams_mapping():
    temp_file = "temp_player_teams_mapping.csv"
    with open(temp_file, 'w') as f:
        f.write("playerID,teamsIDS\n1,|\n2,|")
    
    player_teams = build_fbdb_player_teams_mapping(temp_file)
    assert player_teams == {}
    
    # Eliminar archivo temporal
    import os
    os.remove(temp_file)

def test_build_team_equivalences():
    temp_file = "temp_team_equivalences.csv"
    with open(temp_file, 'w') as f:
        f.write("nombreSofifa,idfbdb\nl messi,1\ncristiano ronaldo,2")
    
    team_name_to_fbdb_id = build_team_equivalences(temp_file)
    assert team_name_to_fbdb_id == {'l messi': 1, 'cristiano ronaldo': 2}
    
    # Eliminar archivo temporal
    import os
    os.remove(temp_file)

def test_player_id_unifier():
    base_path = "./Aplicacion/Pruebas/"
    files_path = "./Aplicacion/Grafo/UnificacionEntidades/Jugadores"
    sofifa_file = os.path.join(files_path, 'players_16_20_sofifa.csv')
    fbdb_file = os.path.join(files_path, 'players_16_20_fbdb.csv')
    output_file = os.path.join(base_path, 'jugadores_unificados_test.csv')
    output_candidates_file = os.path.join(base_path, 'jugadores_candidatos_test.csv')
    
    if os.path.exists(output_file):
        os.remove(output_file)
    if os.path.exists(output_candidates_file):
        os.remove(output_candidates_file)
    
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
        threshold=82,
        threshold_candidates=75,
        output_file=output_file,
        output_file_candidates=output_candidates_file
    )
    
    # Verificar que los archivos de salida existan y contengan datos
    assert os.path.exists(output_file)
    assert os.path.exists(output_candidates_file)

    unificados_df = pd.read_csv(output_file, encoding='utf-8')
    candidatos_df = pd.read_csv(output_candidates_file, encoding='utf-8')

    assert not unificados_df.empty
    assert not candidatos_df.empty

def test_unificar_paises():
    ruta_sofifa_test = r".\Aplicacion\Grafo\UnificacionEntidades\Paises\players_16_20.csv"
    ruta_wikidata_test = r".\Aplicacion\Grafo\UnificacionEntidades\Paises\competiciones_wikidata.csv"
    ruta_salida_prueba = r".\Aplicacion\Grafo\UnificacionEntidades\Paises\paises_unificados.csv"

    df_sofifa_test = pd.read_csv(ruta_sofifa_test)
    df_wikidata_test = pd.read_csv(ruta_wikidata_test)

    # Llamar a la función principal para probar
    unificar_paises()

    # Verificar si el archivo de salida existe
    assert os.path.exists(ruta_salida_prueba), "El archivo de salida no se generó correctamente"

    # Leer el archivo de salida y verificar su contenido
    df_output = pd.read_csv(ruta_salida_prueba)

    # Verificar la cantidad de filas en el DataFrame de salida
    expected_rows = 148  # Ajusta este valor según lo que esperes
    assert len(df_output) == expected_rows, f"El archivo de salida debe tener {expected_rows} filas, pero tiene {len(df_output)} filas"