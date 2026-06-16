import pandas as pd
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
    output_filename = f"teams_{start_str}_{end_str}_sofifa.csv"
    output_path = current_dir / output_filename

    for row in combined_df.itertuples():
        formation = row.formation

        # Reemplazar la columna "formation" con la formacion traducida
        combined_df.at[row.Index, "formation"] =  map_formation(formation)

    # Guardar el archivo combinado
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"[OK] Archivo guardado: {output_filename}")
    
    return True

def map_formation(formation):
    """
    Mapea la formacion traducida al español.
    """
    formation_mapping = {
        "3-4-3 Flat": "3-4-3 En linea",
        "4-1-2-1-2 Narrow": "4-1-2-1-2 Cerrado",
        "4-1-2-1-2 Wide": "4-1-2-1-2 Abierto",
        "4-2-3-1 Narrow": "4-2-3-1 Cerrado",
        "4-2-3-1 Wide": "4-2-3-1 Abierto",
        "4-3-3 Attack": "4-3-3 Ofensivo",
        "4-3-3 Defense": "4-3-3 Defensivo",
        "4-3-3 False 9": "4-3-3 Falso 9",
        "4-3-3 Flat": "4-3-3 En linea",
        "4-3-3 Holding": "4-3-3 Contencion",
        "4-4-1-1 Attack": "4-4-1-1 Ofensivo",
        "4-4-1-1 Midfield": "4-4-1-1 Mediocentro",
        "4-4-2 Flat": "4-4-2 En linea",
        "4-4-2 Holding": "4-4-2 Contencion",
        "4-5-1 Flat": "4-5-1 En linea",
        "5-4-1 Flat": "5-4-1 En linea",
    }
    
    return formation_mapping.get(formation, formation)  # Devuelve la formacion original si no está en el mapeo

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
    output_filename = f"players_{start_str}_{end_str}_sofifa.csv"
    output_path = current_dir / output_filename
    
    for row in combined_df.itertuples():
        positions = row.positions

        positions_list = positions.split(" ")

        positions_final_list = []

        for position in positions_list:
            position_final = map_position(position)
            positions_final_list.append(position_final)

        best_position =  map_position(row.best_position)

        # Reemplazar la columna "positions" con la lista de posiciones traducidas
        combined_df.at[row.Index, "positions"] = " / ".join(positions_final_list)
        combined_df.at[row.Index, "best_position"] = best_position

    # Guardar el archivo combinado
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"[OK] Archivo guardado: {output_filename}")


def map_position(position):
    """
    Mapea la posición de un jugador al español.
    """
    position_mapping = {
        "GK": "Portero", "CB": "Central", "LB": "Lateral Izquierdo", "RB": "Lateral Derecho",
        "LWB": "Carrilero Izquierdo", "RWB": "Carrilero Derecho", "CDM": "Pivote Defensivo",
        "CM": "Mediocentro", "CAM": "Mediapunta", "LM": "Medio izquierdo", "RM": "Medio derecho",
        "LW": "Extremo izquierdo", "RW": "Extremo derecho",  "CF": "Segundo delantero", "ST": "Delantero"
    }
    
    return position_mapping.get(position, position)  # Devuelve la posición original si no está en el mapeo


def main():
    # Configura los años que deseas combinar entre 2010 y 2022
    start_year = 2016
    end_year = 2020
    combine_team_files(start_year, end_year)
    combine_player_files(start_year, end_year)

if __name__ == "__main__":
    main()
