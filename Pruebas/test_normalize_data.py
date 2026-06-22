import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pandas as pd
from Fuentes.kaggle.footballdatabase.kaggleFootbalDatabaseParser import procesarTemporada, procesarEquiposTemporada
from Fuentes.csv_sofifa.sofifaFilter import combine_team_files, combine_player_files

def test_procesarTemporada():
    # Configura las variables necesarias para la prueba
    ano_inicial = 2016
    ano_final = 2020
    
    # Llama a la función del script
    procesarTemporada(ano_inicial, ano_final)
    
    # Verifica que los archivos de salida existan

    games_output_path = os.path.join(root_dir, "Fuentes", "kaggle", "footballdatabase", "generados", "games_16_20_fbdb.csv")
    appearances_output_path = os.path.join(root_dir, "Fuentes", "kaggle", "footballdatabase", "generados", "appearances_16_20_fbdb.csv")
    
    assert pd.read_csv(games_output_path).shape[0] > 0
    assert pd.read_csv(appearances_output_path).shape[0] > 0

def test_procesarEquiposTemporada():
    # Configura las variables necesarias para la prueba
    ano_inicial = 2016
    ano_final = 2020
    
    # Llama a la función del script
    procesarEquiposTemporada(ano_inicial, ano_final)
    
    # Verifica que el archivo de salida exista
    teamstats_output_path = os.path.join(root_dir, "Fuentes", "kaggle", "footballdatabase", "generados", "teamstats_16_20_fbdb.csv")
    
    assert pd.read_csv(teamstats_output_path).shape[0] > 0

def test_combine_team_files():
    # Configura las variables necesarias para la prueba
    start_year = 2016
    end_year = 2020
    
    # Llama a la función del script
    combined_teams = combine_team_files(start_year, end_year)
    
    # Verifica que el archivo de salida exista y tenga datos
    start_year = str(start_year)
    end_year = str(end_year)
    output_filename = f"teams_{start_year[2:]}_{end_year[2:]}_sofifa.csv"
    output_path = root_dir / "Fuentes" / "csv_sofifa" / output_filename

    assert output_path.exists()
    combined_df = pd.read_csv(output_path)
    assert not combined_df.empty

def test_combine_player_files():
    # Configura las variables necesarias para la prueba
    start_year = 2016
    end_year = 2020
    
    # Llama a la función del script
    combined_players = combine_player_files(start_year, end_year)
    
    # Verifica que el archivo de salida exista y tenga datos
    start_year = str(start_year)
    end_year = str(end_year)
    output_filename = f"players_{start_year[2:]}_{end_year[2:]}_sofifa.csv"
    output_path = root_dir / "Fuentes" / "csv_sofifa" / output_filename

    assert output_path.exists()
    combined_df = pd.read_csv(output_path)
    assert not combined_df.empty