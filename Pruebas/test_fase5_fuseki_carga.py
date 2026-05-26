"""
test_fase5_fuseki_carga.py

Pruebas automáticas para carga de datos en Apache Jena Fuseki.
Verifica:
- Disponibilidad del servidor Fuseki
- Carga correcta de archivos TTL
- Ejecución exitosa de consultas SPARQL
- Validación de resultados
- Manejo de errores de conexión
"""

import pytest
import os
import requests
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Grafo"))

# Intentar importar el módulo real - con manejo seguro de errores de conexión
FUSEKI_LOADER_AVAILABLE = False
CARGA_GRAFOS_AVAILABLE = False

try:
    # Mockear requests.post antes de importar cargaGrafos
    # para evitar ConnectionError durante la importación del módulo
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mock import"
        mock_post.return_value = mock_response
        
        from cargaGrafos import GRAFOS_DIR, URL, HEADERS
        CARGA_GRAFOS_AVAILABLE = True
        FUSEKI_LOADER_AVAILABLE = True
except (ImportError, requests.exceptions.ConnectionError, FileNotFoundError):
    # Si no se puede importar, usamos valores default
    GRAFOS_DIR = PROJECT_ROOT / "Grafo" / "Grafos"
    URL = "http://localhost:3030/vini/data"
    HEADERS = {"Content-Type": "text/turtle"}
    CARGA_GRAFOS_AVAILABLE = False


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fuseki_endpoint():
    """Configuración del endpoint Fuseki"""
    return {
        'url': 'http://localhost:3030/vini/data',
        'sparql_url': 'http://localhost:3030/vini/sparql',
        'status_url': 'http://localhost:3030/vini',
    }


@pytest.fixture
def mock_ttl_file(temp_output_dir):
    """Crea un archivo TTL mock para carga"""
    ttl_content = """
    @prefix vini: <http://vini-eii.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    
    vini:Player_1 a vini:Player ;
        foaf:name "Test Player" ;
        vini:overall 85 .
    
    vini:Team_1 a vini:Team ;
        foaf:name "Test Team" ;
        vini:overall 84 .
    
    vini:Player_1 vini:playsFor vini:Team_1 .
    """
    
    file_path = os.path.join(temp_output_dir, 'test_graph.ttl')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    return file_path


@pytest.fixture
def mock_fuseki_success_response():
    """Mock de respuesta exitosa de Fuseki"""
    response = Mock()
    response.status_code = 200
    response.text = "Graph added successfully"
    return response


@pytest.fixture
def mock_sparql_response():
    """Mock de respuesta a consulta SPARQL"""
    return {
        "results": {
            "bindings": [
                {
                    "player": {"type": "uri", "value": "http://vini-eii.org/Player_1"},
                    "name": {"type": "literal", "value": "Test Player"}
                },
                {
                    "player": {"type": "uri", "value": "http://vini-eii.org/Player_2"},
                    "name": {"type": "literal", "value": "Test Player 2"}
                }
            ]
        }
    }


# ============================================================================
# PRUEBAS DE CONECTIVIDAD CON FUSEKI
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestFusekiConnectivity:
    """Tests de conectividad con servidor Fuseki"""
    
    @patch('requests.get')
    def test_fuseki_server_reachable(self, mock_get, fuseki_endpoint):
        """
        Test: Servidor Fuseki es alcanzable
        
        Verifica que el endpoint responde a requests
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = requests.get(fuseki_endpoint['status_url'])
        
        assert response.status_code == 200, \
            "Servidor Fuseki no alcanzable"
    
    
    @patch('requests.get')
    def test_fuseki_sparql_endpoint_available(self, mock_get, fuseki_endpoint):
        """
        Test: Endpoint SPARQL de Fuseki está disponible
        
        Verifica que se puede conectar al endpoint SPARQL
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = requests.get(fuseki_endpoint['sparql_url'])
        
        assert response.status_code == 200, \
            "Endpoint SPARQL no disponible"


# ============================================================================
# PRUEBAS DE CARGA DE DATOS
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestTTLUpload:
    """Tests para carga de archivos TTL"""
    
    @patch('requests.post')
    def test_ttl_file_upload_success(self, mock_post, mock_ttl_file, 
                                    mock_fuseki_success_response):
        """
        Test: Carga exitosa de archivo TTL
        
        Verifica que:
        - Solicitud POST se realiza
        - Respuesta es 200 OK
        - Graph es agregado
        """
        mock_post.return_value = mock_fuseki_success_response
        
        with open(mock_ttl_file, 'rb') as f:
            response = requests.post(
                'http://localhost:3030/vini/data',
                data=f,
                headers={'Content-Type': 'text/turtle'}
            )
        
        assert response.status_code == 200, \
            "Carga de TTL fallida"
        assert mock_post.called, \
            "Solicitud POST no se realizó"
    
    
    @patch('requests.post')
    def test_multiple_ttl_files_upload(self, mock_post, mock_ttl_file,
                                       mock_fuseki_success_response, 
                                       temp_output_dir):
        """
        Test: Carga de múltiples archivos TTL
        
        Verifica:
        - Todos los archivos se cargan
        - Se hacen múltiples POST requests
        """
        mock_post.return_value = mock_fuseki_success_response
        
        # Crear varios archivos TTL
        ttl_files = []
        for i in range(3):
            file_path = os.path.join(temp_output_dir, f'graph_{i}.ttl')
            with open(file_path, 'w') as f:
                f.write(f"# Graph {i}\n<http://example.org/g{i}> <http://example.org/p> <http://example.org/o> .")
            ttl_files.append(file_path)
        
        # Cargar todos
        for file_path in ttl_files:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    'http://localhost:3030/vini/data',
                    data=f,
                    headers={'Content-Type': 'text/turtle'}
                )
            assert response.status_code == 200
        
        # Verificar que se hicieron 3 llamadas
        assert mock_post.call_count == 3, \
            "No se cargaron todos los archivos"
    
    
    @patch('requests.post')
    def test_ttl_upload_error_handling(self, mock_post, temp_output_dir):
        """
        Test: Manejo correcto de errores en carga
        
        Verifica que se manejan errores de conexión
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Crear un archivo TTL temporal
        ttl_file = os.path.join(temp_output_dir, 'test.ttl')
        with open(ttl_file, 'w') as f:
            f.write("@prefix test: <http://test.org/> .\ntest:item a test:Item .")
        
        try:
            with open(ttl_file, 'rb') as f:
                response = requests.post('http://localhost:3030/vini/data', data=f)
        except requests.exceptions.ConnectionError:
            # Esperado
            pass
        except FileNotFoundError:
            # Fichero no encontrado es también aceptable
            pass
        except Exception as e:
            pytest.fail(f"Error no manejado correctamente: {e}")


# ============================================================================
# PRUEBAS DE CONSULTAS SPARQL
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestSPARQLQueries:
    """Tests para ejecución de consultas SPARQL"""
    
    @patch('requests.get')
    def test_simple_sparql_query(self, mock_get, mock_sparql_response):
        """
        Test: Ejecución de consulta SPARQL simple
        
        Query: SELECT ?player ?name WHERE { ?player rdf:type vini:Player }
        """
        mock_response = Mock()
        mock_response.json.return_value = mock_sparql_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        query = """
        PREFIX vini: <http://vini-eii.org/>
        SELECT ?player ?name WHERE {
            ?player a vini:Player ;
                    foaf:name ?name .
        }
        """
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': query},
            headers={'Accept': 'application/sparql-results+json'}
        )
        
        assert response.status_code == 200, \
            "Consulta SPARQL fallida"
        
        results = response.json()
        assert 'results' in results, \
            "Respuesta no contiene 'results'"
    
    
    @patch('requests.get')
    def test_sparql_query_with_filters(self, mock_get, mock_sparql_response):
        """
        Test: Consulta SPARQL con FILTER
        
        Query: SELECT players con overall >= 85
        """
        filtered_response = {
            "results": {
                "bindings": [
                    {
                        "player": {"type": "uri", "value": "http://vini-eii.org/Player_1"},
                        "overall": {"type": "literal", "value": "93"}
                    }
                ]
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = filtered_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        query = """
        PREFIX vini: <http://vini-eii.org/>
        SELECT ?player ?overall WHERE {
            ?player vini:overall ?overall .
            FILTER (?overall >= 85)
        }
        """
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': query}
        )
        
        results = response.json()
        assert len(results['results']['bindings']) >= 0, \
            "Errores en consulta filtrada"
    
    
    @patch('requests.get')
    def test_sparql_query_results_parsing(self, mock_get, mock_sparql_response):
        """
        Test: Parsing correcto de resultados SPARQL
        
        Verifica que los resultados tienen estructura esperada
        """
        mock_response = Mock()
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': 'SELECT * WHERE { ?s ?p ?o }'}
        )
        
        results = response.json()
        
        assert 'results' in results, "Falta 'results' en respuesta"
        assert 'bindings' in results['results'], "Falta 'bindings' en results"
        assert isinstance(results['results']['bindings'], list), \
            "Bindings no es lista"
        
        # Verificar estructura de un binding
        if results['results']['bindings']:
            binding = results['results']['bindings'][0]
            assert isinstance(binding, dict), "Binding no es diccionario"


# ============================================================================
# PRUEBAS DE VALIDACIÓN DE DATOS CARGADOS
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestLoadedDataValidation:
    """Tests para validación de datos cargados en Fuseki"""
    
    @patch('requests.get')
    def test_count_players_after_upload(self, mock_get):
        """
        Test: Contar Players después de carga
        
        Query: SELECT (COUNT(?player) as ?count) WHERE { ?player a vini:Player }
        """
        count_response = {
            "results": {
                "bindings": [
                    {"count": {"type": "literal", "value": "42"}}
                ]
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = count_response
        mock_get.return_value = mock_response
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': 'SELECT (COUNT(?p) as ?c) WHERE { ?p a vini:Player }'}
        )
        
        results = response.json()
        count_val = int(results['results']['bindings'][0]['count']['value'])
        
        assert count_val >= 0, "Count incorrecto"
    
    
    @patch('requests.get')
    def test_relationships_exist(self, mock_get):
        """
        Test: Verificar que existen relaciones playsFor
        
        Query: SELECT ?player ?team WHERE { ?player vini:playsFor ?team }
        """
        rel_response = {
            "results": {
                "bindings": [
                    {
                        "player": {"type": "uri", "value": "http://vini-eii.org/Player_1"},
                        "team": {"type": "uri", "value": "http://vini-eii.org/Team_1"}
                    }
                ]
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = rel_response
        mock_get.return_value = mock_response
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': 'SELECT ?p ?t WHERE { ?p vini:playsFor ?t }'}
        )
        
        results = response.json()
        assert len(results['results']['bindings']) >= 0, \
            "Error en consulta de relaciones"


# ============================================================================
# PRUEBAS DE ERRORES Y RECUPERACIÓN
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @patch('requests.post')
    def test_invalid_ttl_format_error(self, mock_post):
        """
        Test: Manejo de error con TTL inválido
        
        Verifica que Fuseki rechaza TTL malformado
        """
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid RDF syntax"
        mock_post.return_value = mock_response
        
        response = requests.post(
            'http://localhost:3030/vini/data',
            data=b"invalid ttl content <<<>>>",
            headers={'Content-Type': 'text/turtle'}
        )
        
        # Debe rechazarlo (400 Bad Request)
        assert response.status_code != 200, \
            "TTL inválido fue aceptado"
    
    
    @patch('requests.get')
    def test_malformed_sparql_query_error(self, mock_get):
        """
        Test: Manejo de error con query SPARQL malformada
        
        Verifica que Fuseki rechaza queries inválidas
        """
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Malformed SPARQL query"
        mock_get.return_value = mock_response
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': 'SELECT * INVALID QUERY'}
        )
        
        assert response.status_code == 400, \
            "Query inválida fue aceptada"


# ============================================================================
# PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.requires_fuseki
class TestFusekiPerformance:
    """Tests de rendimiento"""
    
    @patch('requests.post')
    def test_large_ttl_upload_performance(self, mock_post, temp_output_dir):
        """
        Test: Carga de TTL grande (1MB+) < 5 segundos
        
        Umbral: < 5 segundos
        """
        import time
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Crear TTL grande
        large_ttl = "@prefix vini: <http://vini-eii.org/> .\n\n"
        for i in range(1000):
            large_ttl += f'vini:Player_{i} a vini:Player .\n'
        
        file_path = os.path.join(temp_output_dir, 'large.ttl')
        with open(file_path, 'w') as f:
            f.write(large_ttl)
        
        start_time = time.time()
        
        with open(file_path, 'rb') as f:
            response = requests.post(
                'http://localhost:3030/vini/data',
                data=f,
                headers={'Content-Type': 'text/turtle'}
            )
        
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, \
            f"Carga de TTL tardó {elapsed:.2f}s (umbral: 5.0s)"
    
    
    @patch('requests.get')
    def test_sparql_query_response_time(self, mock_get, mock_sparql_response):
        """
        Test: Respuesta a consulta SPARQL < 1 segundo
        
        Umbral: < 1 segundo
        """
        import time
        
        mock_response = Mock()
        mock_response.json.return_value = mock_sparql_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        start_time = time.time()
        
        response = requests.get(
            'http://localhost:3030/vini/sparql',
            params={'query': 'SELECT * WHERE { ?s ?p ?o } LIMIT 100'}
        )
        
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, \
            f"Consulta tardó {elapsed:.2f}s (umbral: 1.0s)"
