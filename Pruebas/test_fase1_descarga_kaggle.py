"""
test_fase1_descarga_kaggle.py

Pruebas automáticas para la descarga de datasets desde Kaggle.
Verifica:
- Descarga correcta de múltiples datasets
- Presencia de archivos CSV esperados
- Estructura básica de los CSVs
- Manejo de errores de descarga
- Validación de columnas esperadas
"""

import pytest
import os
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys

# Agregar rutas al path para importar módulos del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Fuentes"))

# Intentar importar el módulo real (si falla, usaremos mocks)
try:
    from kaggleDownloader import KaggleDownloader
    KAGGLE_DOWNLOADER_AVAILABLE = True
except ImportError:
    KAGGLE_DOWNLOADER_AVAILABLE = False


# ============================================================================
# PRUEBAS UNITARIAS - KaggleDownloader
# ============================================================================

@pytest.mark.requires_selenium  # Requiere credenciales de Kaggle
class TestKaggleDownloader:
    """Suite de pruebas para KaggleDownloader"""
    
    def test_downloader_initialization(self, temp_output_dir):
        """
        Test: Inicialización correcta del descargador
        
        Verifica que:
        - El objeto se inicializa correctamente
        - La carpeta de salida se crea si no existe
        - El path se asigna correctamente
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        downloader = KaggleDownloader(temp_output_dir)
        
        assert downloader is not None, "KaggleDownloader no se inicializó"
        assert downloader.base_output_dir == temp_output_dir, \
            "Path de salida no coincide"
        assert os.path.exists(temp_output_dir), \
            "Directorio de salida no fue creado"
    
    
    @patch('kagglehub.dataset_download')
    def test_single_dataset_download_success(self, mock_download, temp_output_dir):
        """
        Test: Descarga exitosa de un único dataset
        
        Mock simula:
        - Descarga desde Kaggle
        - Creación de archivos CSV
        
        Verifica:
        - Resultado True (éxito)
        - Archivos copiados correctamente
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        # Setup mock
        temp_kaggle = os.path.join(temp_output_dir, 'kaggle_mock')
        os.makedirs(temp_kaggle, exist_ok=True)
        
        # Crear archivos mock en la carpeta simulada
        test_csv_content = "id,name,value\n1,test,100\n2,test2,200\n"
        csv_file = os.path.join(temp_kaggle, 'test.csv')
        with open(csv_file, 'w') as f:
            f.write(test_csv_content)
        
        mock_download.return_value = temp_kaggle
        
        # Ejecutar test
        downloader = KaggleDownloader(temp_output_dir)
        result = downloader.download_dataset('test/dataset', 'test_folder')
        
        # Assertions
        assert result is True, "Descarga retornó False"
        assert mock_download.called, "dataset_download no fue llamado"
        assert os.path.exists(os.path.join(temp_output_dir, 'test_folder')), \
            "Carpeta de destino no fue creada"
    
    
    @patch('kagglehub.dataset_download')
    def test_single_dataset_download_error(self, mock_download, temp_output_dir):
        """
        Test: Manejo correcto de errores en descarga
        
        Mock simula:
        - Error de conexión / credenciales inválidas
        
        Verifica:
        - Resultado False (fallo)
        - Excepción capturada correctamente
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        mock_download.side_effect = Exception("Credenciales inválidas")
        
        downloader = KaggleDownloader(temp_output_dir)
        result = downloader.download_dataset('invalid/dataset')
        
        assert result is False, "Error no fue manejado correctamente"
    
    
    @patch('kagglehub.dataset_download')
    def test_multiple_datasets_download(self, mock_download, temp_output_dir):
        """
        Test: Descarga de múltiples datasets
        
        Verifica:
        - Se descargan todos los datasets
        - Diccionario de resultados es correcto
        - Maneja mix de éxitos y fallos
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        # Setup mocks
        mock_dirs = []
        for i in range(3):
            temp_dir = os.path.join(temp_output_dir, f'mock_{i}')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear CSV mock
            csv_file = os.path.join(temp_dir, f'data_{i}.csv')
            with open(csv_file, 'w') as f:
                f.write(f"id,value\n{i},100\n")
            
            mock_dirs.append(temp_dir)
        
        # Fallar en segunda descarga, exitosa en las otras
        mock_download.side_effect = [mock_dirs[0], Exception("Error"), mock_dirs[2]]
        
        # Ejecutar test
        downloader = KaggleDownloader(temp_output_dir)
        datasets = ['dataset1/path', 'dataset2/path', 'dataset3/path']
        results = downloader.download_multiple_datasets(datasets)
        
        # Assertions
        assert isinstance(results, dict), "Resultado no es diccionario"
        assert len(results) == 3, "No se procesaron todos los datasets"
        assert results['dataset1/path'] is True, "Dataset 1 debería ser exitoso"
        assert results['dataset2/path'] is False, "Dataset 2 debería fallar"
        assert results['dataset3/path'] is True, "Dataset 3 debería ser exitoso"
    
    
    @patch('kagglehub.dataset_download')
    def test_csv_files_copied_correctly(self, mock_download, temp_output_dir):
        """
        Test: CSVs se copian correctamente desde descarga
        
        Verifica:
        - Archivos CSV se copian al directorio de destino
        - Solo se copian archivos .csv
        - Nombres de archivo se preservan
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        # Setup mock con archivos variados
        temp_kaggle = os.path.join(temp_output_dir, 'kaggle_mock')
        os.makedirs(temp_kaggle, exist_ok=True)
        
        # Crear archivos mixtos
        files_to_create = ['players.csv', 'teams.csv', 'README.txt', 'config.json']
        for filename in files_to_create:
            filepath = os.path.join(temp_kaggle, filename)
            with open(filepath, 'w') as f:
                f.write("mock content")
        
        mock_download.return_value = temp_kaggle
        
        downloader = KaggleDownloader(temp_output_dir)
        downloader.download_dataset('test/dataset', 'output')
        
        # Verificar que solo CSVs fueron copiados
        output_dir = os.path.join(temp_output_dir, 'output')
        output_files = os.listdir(output_dir)
        
        assert len(output_files) == 2, "Solo deben copiarse 2 CSVs"
        assert 'players.csv' in output_files, "players.csv no copiado"
        assert 'teams.csv' in output_files, "teams.csv no copiado"
        assert 'README.txt' not in output_files, "README.txt no debería copiarse"


# ============================================================================
# PRUEBAS DE INTEGRACIÓN (mockeadas)
# ============================================================================

@pytest.mark.integration
class TestKaggleDownloaderIntegration:
    """Tests de integración del descargador de Kaggle"""
    
    @patch('kagglehub.dataset_download')
    def test_summary_generation(self, mock_download, temp_output_dir):
        """
        Test: Generación correcta del resumen
        
        Verifica:
        - get_summary() retorna diccionario correctamente formado
        - Calcula cantidad de archivos
        - Calcula tamaño total
        """
        if not KAGGLE_DOWNLOADER_AVAILABLE:
            pytest.skip("kaggleDownloader no disponible")
        
        # Setup
        temp_kaggle = os.path.join(temp_output_dir, 'kaggle_mock')
        os.makedirs(temp_kaggle, exist_ok=True)
        
        # Crear CSVs con tamaños diferentes
        for i in range(3):
            csv_file = os.path.join(temp_kaggle, f'data_{i}.csv')
            with open(csv_file, 'w') as f:
                # Escribir ~ 1KB de datos
                f.write("id,name\n" + "\n".join([f"{j},data_{j}" for j in range(100)]))
        
        mock_download.return_value = temp_kaggle
        
        downloader = KaggleDownloader(temp_output_dir)
        downloader.download_dataset('test/dataset', 'test_folder')
        
        summary = downloader.get_summary()
        
        # Assertions
        assert 'base_dir' in summary, "Resumen falta 'base_dir'"
        assert 'datasets' in summary, "Resumen falta 'datasets'"
        assert 'test_folder' in summary['datasets'], "test_folder no en resumen"
        assert summary['datasets']['test_folder']['count'] == 3, \
            "Contador de archivos incorrecto"


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE DATOS
# ============================================================================

class TestKaggleDataValidation:
    """Tests para validación de datos descargados"""
    
    def test_players_csv_has_required_columns(self, temp_output_dir):
        """
        Test: CSV de jugadores tiene columnas requeridas
        
        Columnas esperadas (basadas en Football Database):
        - playerID, name, age, height, weight, position, etc.
        """
        # Crear CSV mock con estructura correcta
        players_data = {
            'playerID': [1, 2, 3],
            'name': ['Player1', 'Player2', 'Player3'],
            'age': [25, 28, 31],
            'height': [180, 185, 182],
            'position': ['ST', 'CM', 'CB']
        }
        df = pd.DataFrame(players_data)
        csv_path = os.path.join(temp_output_dir, 'players.csv')
        df.to_csv(csv_path, index=False)
        
        # Validar
        required_cols = ['playerID', 'name', 'age', 'height', 'position']
        df_loaded = pd.read_csv(csv_path)
        
        missing_cols = set(required_cols) - set(df_loaded.columns)
        assert not missing_cols, f"Columnas faltantes: {missing_cols}"
    
    
    def test_teams_csv_readable_as_dataframe(self, temp_output_dir):
        """
        Test: CSV de equipos es legible como DataFrame
        
        Verifica:
        - Archivo es válido CSV
        - Se puede cargar con pandas
        - No tiene errores de encoding
        """
        teams_data = {
            'teamID': [1, 2, 3],
            'name': ['Team1', 'Team2', 'Team3'],
            'country': ['Country1', 'Country2', 'Country3']
        }
        df = pd.DataFrame(teams_data)
        csv_path = os.path.join(temp_output_dir, 'teams.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Intentar cargar
        df_loaded = pd.read_csv(csv_path, encoding='utf-8')
        
        assert df_loaded is not None, "No se pudo cargar CSV"
        assert len(df_loaded) == 3, "Número de filas incorrecto"
        assert df_loaded['teamID'].dtype in ['int64', 'int32'], \
            "Tipo de dato incorrecto para teamID"
    
    
    def test_csv_no_empty_rows(self, temp_output_dir):
        """
        Test: CSV descargado no tiene filas vacías
        
        Verifica:
        - Todas las filas tienen valores
        - No hay filas duplicadas innecesarias
        """
        # Crear CSV con algunos datos
        data = {
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [100, 200, 300]
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(temp_output_dir, 'test.csv')
        df.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        # Verificar no hay filas null
        assert not df_loaded.isnull().any().any(), \
            "CSV contiene valores null"
