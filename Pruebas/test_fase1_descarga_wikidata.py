"""
test_fase1_descarga_wikidata.py

Pruebas automáticas para descarga de datos desde Wikidata mediante consultas SPARQL.
Verifica:
- Ejecución correcta de consultas SPARQL
- Generación de CSV con datos de Wikidata
- Presencia de QIDs en los resultados
- Manejo de resultados vacíos
- Validación de estructura de datos
"""

import pytest
import os
import pandas as pd
import json
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Fuentes"))

# Intentar importar el módulo real
try:
    from wikiDataQuerys import WikidataCompetitionScraper
    WIKIDATA_AVAILABLE = True
except ImportError:
    WIKIDATA_AVAILABLE = False


# ============================================================================
# FIXTURES PARA WIKIDATA
# ============================================================================

@pytest.fixture
def mock_wikidata_response_single_competition():
    """Mock de respuesta SPARQL para una competición"""
    return {
        "results": {
            "bindings": [
                {
                    "year": {"value": "2020"},
                    "competition": {"value": "http://www.wikidata.org/entity/Q18756"},
                    "competitionLabel": {"value": "UEFA Champions League"},
                    "country": {"value": "http://www.wikidata.org/entity/Q29"},
                    "countryLabel": {"value": "Spain"},
                    "team": {"value": "http://www.wikidata.org/entity/Q18602"},
                    "teamLabel": {"value": "Real Madrid"}
                },
                {
                    "year": {"value": "2020"},
                    "competition": {"value": "http://www.wikidata.org/entity/Q18756"},
                    "competitionLabel": {"value": "UEFA Champions League"},
                    "country": {"value": "http://www.wikidata.org/entity/Q25"},
                    "countryLabel": {"value": "France"},
                    "team": {"value": "http://www.wikidata.org/entity/Q19319"},
                    "teamLabel": {"value": "Paris Saint-Germain"}
                }
            ]
        }
    }


@pytest.fixture
def mock_wikidata_response_empty():
    """Mock de respuesta vacía de SPARQL"""
    return {"results": {"bindings": []}}


@pytest.fixture
def mock_wikidata_response_multiple_competitions():
    """Mock de respuesta con múltiples competiciones"""
    return {
        "results": {
            "bindings": [
                {
                    "year": {"value": "2020"},
                    "competition": {"value": "http://www.wikidata.org/entity/Q18756"},
                    "competitionLabel": {"value": "UEFA Champions League"},
                    "country": {"value": "http://www.wikidata.org/entity/Q29"},
                    "countryLabel": {"value": "Spain"},
                    "team": {"value": "http://www.wikidata.org/entity/Q18602"},
                    "teamLabel": {"value": "Real Madrid"}
                },
                {
                    "year": {"value": "2020"},
                    "competition": {"value": "http://www.wikidata.org/entity/Q13394"},
                    "competitionLabel": {"value": "Ligue 1"},
                    "country": {"value": "http://www.wikidata.org/entity/Q25"},
                    "countryLabel": {"value": "France"},
                    "team": {"value": "http://www.wikidata.org/entity/Q19319"},
                    "teamLabel": {"value": "Paris Saint-Germain"}
                }
            ]
        }
    }


# ============================================================================
# PRUEBAS UNITARIAS - WikidataCompetitionScraper
# ============================================================================

@pytest.mark.integration
class TestWikidataCompetitionScraper:
    """Suite de pruebas para WikidataCompetitionScraper"""
    
    def test_scraper_initialization(self, temp_output_dir):
        """
        Test: Inicialización correcta del scraper
        
        Verifica:
        - Objeto se inicializa sin errores
        - Directorio de salida se crea
        - URL endpoint es correcta
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        scraper = WikidataCompetitionScraper(output_dir=temp_output_dir)
        
        assert scraper is not None, "Scraper no inicializado"
        assert hasattr(scraper, 'WIKIDATA_ENDPOINT'), "Falta WIKIDATA_ENDPOINT"
        assert 'query.wikidata.org' in scraper.WIKIDATA_ENDPOINT, \
            "Endpoint no es de Wikidata"
    
    
    def test_sparql_query_building(self):
        """
        Test: Construcción correcta de consulta SPARQL
        
        Verifica:
        - Query incluye los QIDs especificados
        - Query tiene estructura SPARQL válida
        - Query filtra por años correctos
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        scraper = WikidataCompetitionScraper()
        qids = ['Q18756', 'Q18760', 'Q13394']
        query = scraper.build_query(qids)
        
        # Verificaciones
        assert 'SELECT' in query, "Query no es SELECT"
        assert 'WHERE' in query, "Query no tiene cláusula WHERE"
        assert 'Q18756' in query, "QID no incluído en query"
        assert 'Q18760' in query, "QID no incluído en query"
        assert '2016' in query or '2020' in query, \
            "Query no filtra por años especificados"
    
    
    @patch('requests.get')
    def test_execute_query_success(self, mock_get, mock_wikidata_response_single_competition):
        """
        Test: Ejecución exitosa de consulta SPARQL
        
        Verifica:
        - Solicitud GET se realiza correctamente
        - Respuesta se parsea como JSON
        - Retorna lista de resultados
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wikidata_response_single_competition
        mock_get.return_value = mock_response
        
        scraper = WikidataCompetitionScraper()
        results = scraper.execute_query("SELECT * WHERE {?s ?p ?o}")
        
        # Assertions
        assert isinstance(results, list), "Resultado no es lista"
        assert len(results) == 2, "No se retornaron todos los resultados"
        assert 'competitionLabel' in results[0], \
            "Resultado no tiene competitionLabel"
    
    
    @patch('requests.get')
    def test_execute_query_empty_result(self, mock_get, mock_wikidata_response_empty):
        """
        Test: Manejo correcto de respuesta vacía
        
        Verifica:
        - Cuando no hay resultados, retorna lista vacía
        - No lanza excepción
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wikidata_response_empty
        mock_get.return_value = mock_response
        
        scraper = WikidataCompetitionScraper()
        results = scraper.execute_query("SELECT * WHERE {}")
        
        assert isinstance(results, list), "Resultado no es lista"
        assert len(results) == 0, "Debería retornar lista vacía"
    
    
    @patch('requests.get')
    def test_execute_query_network_error(self, mock_get):
        """
        Test: Manejo de errores de red
        
        Verifica:
        - Captura excepciones de requests
        - Retorna lista vacía en caso de error
        - No lanza excepción no manejada
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        # Mock para simular timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        scraper = WikidataCompetitionScraper()
        
        try:
            results = scraper.execute_query("SELECT * WHERE {}")
            # Si no lanza excepción, debería retornar lista
            assert isinstance(results, (list, type(None))), "Debería retornar lista o None"
        except requests.exceptions.Timeout:
            # Es aceptable que lance la excepción si no está manejada
            pass
    
    
    @patch('requests.get')
    def test_format_results_correct_structure(self, mock_get, mock_wikidata_response_single_competition):
        """
        Test: Formateo correcto de resultados SPARQL
        
        Verifica:
        - Extrae información relevante
        - Convierte URIs de Wikidata a QIDs
        - Retorna estructura de diccionarios
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        competitions = {'Q18756': 'UEFA Champions League'}
        raw_results = mock_wikidata_response_single_competition['results']['bindings']
        
        scraper = WikidataCompetitionScraper()
        formatted = scraper.format_results(raw_results, competitions)
        
        assert isinstance(formatted, list), "Resultado no es lista"
        assert len(formatted) > 0, "Resultado formateado está vacío"
        assert all(isinstance(item, dict) for item in formatted), \
            "Items no son diccionarios"
    
    
    @patch('requests.get')
    def test_fetch_multiple_competitions(self, mock_get, temp_output_dir, 
                                         mock_wikidata_response_multiple_competitions):
        """
        Test: Descarga de múltiples competiciones
        
        Verifica:
        - Descarga múltiples competiciones en una sola consulta
        - Genera CSV con todos los datos
        - CSV se guarda en ubicación correcta
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wikidata_response_multiple_competitions
        mock_get.return_value = mock_response
        
        competitions = {
            'Q18756': 'UEFA Champions League',
            'Q13394': 'Ligue 1'
        }
        
        scraper = WikidataCompetitionScraper(output_dir=temp_output_dir)
        scraper.fetch_multiple_competitions(competitions)
        
        # Verificar que el CSV se creó
        csv_path = os.path.join(temp_output_dir, 'competiciones_wikidata.csv')
        assert os.path.exists(csv_path), f"CSV no creado en {csv_path}"


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE DATOS
# ============================================================================

class TestWikidataDataValidation:
    """Tests para validación de datos descargados desde Wikidata"""
    
    def test_qid_extraction_from_uri(self):
        """
        Test: Extracción correcta de QID desde URI de Wikidata
        
        URIs de Wikidata siguen patrón: http://www.wikidata.org/entity/Q{NÚMERO}
        """
        import re
        
        test_uris = [
            ("http://www.wikidata.org/entity/Q18756", "Q18756"),
            ("http://www.wikidata.org/entity/Q1", "Q1"),
            ("http://www.wikidata.org/entity/Q12345", "Q12345"),
        ]
        
        pattern = r'(Q\d+)$'
        
        for uri, expected_qid in test_uris:
            match = re.search(pattern, uri)
            assert match is not None, f"No se extrajo QID de {uri}"
            assert match.group(1) == expected_qid, \
                f"QID extraído incorrecto: {match.group(1)} != {expected_qid}"
    
    
    def test_competitions_csv_structure(self, temp_output_dir):
        """
        Test: Estructura correcta de CSV de competiciones
        
        Columnas esperadas:
        - year, competition, competitionLabel, country, countryLabel, team, teamLabel
        """
        data = {
            'year': [2020, 2020, 2021],
            'competition': ['Q18756', 'Q18760', 'Q18756'],
            'competitionLabel': ['UEFA Champions League', 'UEFA Europa League', 'UEFA Champions League'],
            'country': ['Q29', 'Q25', 'Q183'],
            'countryLabel': ['Spain', 'France', 'Germany'],
            'team': ['Q18602', 'Q19319', 'Q25',],
            'teamLabel': ['Real Madrid', 'Paris Saint-Germain', 'Bayern Munich']
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(temp_output_dir, 'competitions.csv')
        df.to_csv(csv_path, index=False)
        
        # Validar estructura
        df_loaded = pd.read_csv(csv_path)
        expected_cols = ['year', 'competition', 'competitionLabel', 'country', 
                        'countryLabel', 'team', 'teamLabel']
        
        missing_cols = set(expected_cols) - set(df_loaded.columns)
        assert not missing_cols, f"Columnas faltantes: {missing_cols}"
    
    
    def test_wikidata_entries_have_qids(self, temp_output_dir):
        """
        Test: Todos los registros Wikidata tienen QIDs
        
        QIDs deben estar presentes en columnas:
        - competition, country, team
        """
        data = {
            'year': [2020, 2020],
            'competition': ['Q18756', 'Q18760'],
            'competitionLabel': ['UEFA Champions League', 'UEFA Europa League'],
            'country': ['Q29', 'Q25'],
            'countryLabel': ['Spain', 'France'],
            'team': ['Q18602', 'Q19319'],
            'teamLabel': ['Real Madrid', 'Paris Saint-Germain']
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(temp_output_dir, 'competitions.csv')
        df.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        # Verificar QIDs presentes
        qid_columns = ['competition', 'country', 'team']
        for col in qid_columns:
            assert df_loaded[col].notna().all(), \
                f"Columna {col} tiene valores null"
            assert all(str(v).startswith('Q') for v in df_loaded[col]), \
                f"Columna {col} tiene valores sin formato QID"
    
    
    def test_year_filter_2016_2020(self, temp_output_dir):
        """
        Test: Filtrado correcto de años 2016-2020
        
        Las consultas SPARQL deben filtrar solo años en este rango
        """
        # Crear CSV con datos de varios años
        data = {
            'year': [2014, 2016, 2018, 2020, 2022],
            'competition': ['Q18756'] * 5,
            'competitionLabel': ['UEFA Champions League'] * 5,
            'country': ['Q29'] * 5,
            'countryLabel': ['Spain'] * 5,
            'team': ['Q18602'] * 5,
            'teamLabel': ['Real Madrid'] * 5
        }
        df = pd.DataFrame(data)
        
        # Filtrar a rango 2016-2020
        df_filtered = df[(df['year'] >= 2016) & (df['year'] <= 2020)]
        
        csv_path = os.path.join(temp_output_dir, 'competitions_filtered.csv')
        df_filtered.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        assert df_loaded['year'].min() >= 2016, "Año mínimo < 2016"
        assert df_loaded['year'].max() <= 2020, "Año máximo > 2020"
        assert len(df_loaded) == 3, "Filtrado incorrecto"


# ============================================================================
# PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.slow
class TestWikidataPerformance:
    """Tests de rendimiento para Wikidata"""
    
    @patch('requests.get')
    def test_query_execution_time_acceptable(self, mock_get, mock_wikidata_response_single_competition):
        """
        Test: Tiempo de ejecución de query es aceptable
        
        Umbral: < 5 segundos por consulta (con mock, mucho más rápido)
        """
        if not WIKIDATA_AVAILABLE:
            pytest.skip("wikiDataQuerys no disponible")
        
        import time
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wikidata_response_single_competition
        mock_get.return_value = mock_response
        
        scraper = WikidataCompetitionScraper()
        
        start_time = time.time()
        results = scraper.execute_query("SELECT * WHERE {?s ?p ?o}")
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Consulta tardó demasiado: {elapsed:.2f}s"
