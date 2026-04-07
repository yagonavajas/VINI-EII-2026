import pandas as pd
import sys
from pathlib import Path

def combine_team_files(start_year, end_year):
    """
    Combina archivos de equipos (teams_YYYY.csv) desde start_year hasta end_year
    en un único archivo llamado teams_SS_EE.csv
    """
    
    current_dir = Path(__file__).parent
    all_dfs = []
    
    # Leer cada archivo de año
    for year in range(start_year, end_year + 1):
        file_path = current_dir / f"teams_{year}.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            df['year'] = year
            all_dfs.append(df)
            print(f"[+] {file_path.name} cargado")
        else:
            print(f"[!] {file_path.name} no encontrado")
    
    if not all_dfs:
        print(f"[ERROR] No se encontraron archivos")
        return False
    
    # Combinar todos los dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Generar nombre del archivo de salida
    start_str = str(start_year)[2:]
    end_str = str(end_year)[2:]
    output_filename = f"teams_{start_str}_{end_str}.csv"
    output_path = current_dir / output_filename
    
    # Guardar el archivo combinado
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"[OK] Archivo guardado: {output_filename}")
    
    return True

def combine_player_files(start_year, end_year):
    """
    Combina archivos de jugadores (players_YYYY.csv) desde start_year hasta end_year
    en un único archivo llamado players_SS_EE.csv
    """
    
    current_dir = Path(__file__).parent
    all_dfs = []
    
    # Leer cada archivo de año
    for year in range(start_year, end_year + 1):
        file_path = current_dir / f"players_{year}.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            df['year'] = year
            all_dfs.append(df)
            print(f"[+] {file_path.name} cargado")
        else:
            print(f"[!] {file_path.name} no encontrado")
    
    if not all_dfs:
        print(f"[ERROR] No se encontraron archivos")
        return False
    
    # Combinar todos los dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Generar nombre del archivo de salida
    start_str = str(start_year)[2:]
    end_str = str(end_year)[2:]
    output_filename = f"players_{start_str}_{end_str}.csv"
    output_path = current_dir / output_filename
    
    # Guardar el archivo combinado
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"[OK] Archivo guardado: {output_filename}")
    
    return True

def main():
    start_year = 2015
    end_year = 2020
    combine_team_files(start_year, end_year)
    combine_player_files(start_year, end_year)

if __name__ == "__main__":
    main()
