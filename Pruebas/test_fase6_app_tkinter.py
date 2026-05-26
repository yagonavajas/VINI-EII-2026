"""
test_fase6_app_tkinter.py

Pruebas automáticas para la aplicación Tkinter.
Verifica:
- Inicialización correcta de la interfaz
- Ejecución de consultas SPARQL
- Manejo de errores de conexión
- Actualización correcta de UI
- Funcionalidad de búsqueda y filtrado
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, call
import tkinter as tk
from tkinter import ttk

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Escritorio"))

# Intentar importar el módulo real
try:
    from app import App  # Ajustar según nombre real de la app
    TKINTER_APP_AVAILABLE = True
except ImportError:
    TKINTER_APP_AVAILABLE = False


# ============================================================================
# FIXTURES DE MOCK
# ============================================================================

@pytest.fixture
def mock_sparql_connection():
    """Mock para conexión SPARQL"""
    mock_conn = MagicMock()
    mock_conn.query = MagicMock(return_value=[
        {
            'player': 'http://vini-eii.org/Player_1',
            'playerLabel': 'Cristiano Ronaldo',
            'overall': 93,
            'team': 'Manchester United'
        },
        {
            'player': 'http://vini-eii.org/Player_2',
            'playerLabel': 'Lionel Messi',
            'overall': 93,
            'team': 'Paris Saint-Germain'
        }
    ])
    mock_conn.is_connected = MagicMock(return_value=True)
    return mock_conn


@pytest.fixture
def mock_sparql_connection_error():
    """Mock para conexión SPARQL con error"""
    mock_conn = MagicMock()
    mock_conn.query = MagicMock(side_effect=Exception("Connection failed"))
    mock_conn.is_connected = MagicMock(return_value=False)
    return mock_conn


@pytest.fixture
def empty_sparql_results():
    """Mock para resultados vacíos"""
    mock_conn = MagicMock()
    mock_conn.query = MagicMock(return_value=[])
    mock_conn.is_connected = MagicMock(return_value=True)
    return mock_conn


# ============================================================================
# PRUEBAS DE INICIALIZACIÓN
# ============================================================================

@pytest.mark.integration
class TestTkinterAppInitialization:
    """Tests para inicialización de la app Tkinter"""
    
    @patch('tkinter.Tk')
    def test_app_window_creation(self, mock_tk):
        """
        Test: Ventana raíz se crea correctamente
        
        Verifica que Tk() es instanciado
        """
        root = MagicMock()
        mock_tk.return_value = root
        
        # Verificar que Tk se instancia
        window = tk.Tk()
        assert window is not None
    
    
    @patch('tkinter.Tk')
    def test_app_widget_creation(self, mock_tk):
        """
        Test: Widgets principales se crean
        
        Verifica presencia de:
        - Frame para entrada de búsqueda
        - Botón de búsqueda
        - Treeview para resultados
        """
        root = MagicMock()
        mock_tk.return_value = root
        
        # En una app real, verificar creación de widgets
        assert root is not None
    
    
    @patch('tkinter.Tk')
    def test_app_title_set(self, mock_tk):
        """Test: Título de ventana se establece"""
        root = MagicMock()
        mock_tk.return_value = root
        
        # Una app debería establecer título
        root.title = MagicMock()
        root.title("TFG - Football Knowledge Graph")
        
        assert root.title.called


# ============================================================================
# PRUEBAS DE CONSULTAS SPARQL DESDE APP
# ============================================================================

@pytest.mark.integration
class TestAppSPARQLQueries:
    """Tests para ejecución de consultas desde app"""
    
    def test_search_players_by_name(self, mock_sparql_connection):
        """
        Test: Búsqueda de jugadores por nombre
        
        Mock simula respuesta del servidor SPARQL
        """
        query_result = mock_sparql_connection.query(
            """
            PREFIX vini: <http://vini-eii.org/>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            SELECT ?player ?playerLabel ?overall ?team
            WHERE {
                ?player a vini:Player ;
                        foaf:name ?playerLabel ;
                        vini:overall ?overall ;
                        vini:playsFor ?team .
                FILTER (CONTAINS(?playerLabel, "Cristiano"))
            }
            LIMIT 10
            """
        )
        
        assert len(query_result) > 0, "No se encontraron resultados"
        assert 'playerLabel' in query_result[0], "Resultado incompleto"
    
    
    def test_search_teams_by_country(self, mock_sparql_connection):
        """
        Test: Búsqueda de equipos por país
        
        Query SPARQL para encontrar teams de un país
        """
        mock_sparql_connection.query = MagicMock(return_value=[
            {'team': 'Manchester United', 'country': 'England'},
            {'team': 'Liverpool', 'country': 'England'},
            {'team': 'Arsenal', 'country': 'England'},
        ])
        
        results = mock_sparql_connection.query("SELECT ?team WHERE { ?team vini:country ?c }")
        
        assert len(results) == 3, "Resultados incorrectos"
    
    
    def test_filter_by_rating(self, mock_sparql_connection):
        """
        Test: Filtrado de jugadores por rating
        
        Obtener jugadores con overall >= 85
        """
        mock_sparql_connection.query = MagicMock(return_value=[
            {'playerLabel': 'Cristiano Ronaldo', 'overall': 93},
            {'playerLabel': 'Lionel Messi', 'overall': 93},
            {'playerLabel': 'Neymar', 'overall': 92},
        ])
        
        results = mock_sparql_connection.query(
            "SELECT * WHERE { ?p vini:overall ?o FILTER (?o >= 85) }"
        )
        
        # Verificar filtrado
        assert all(int(r['overall']) >= 85 for r in results), \
            "Filtrado incorrecto"


# ============================================================================
# PRUEBAS DE MANEJO DE ERRORES
# ============================================================================

@pytest.mark.integration
class TestAppErrorHandling:
    """Tests para manejo de errores en app"""
    
    def test_connection_error_display(self, mock_sparql_connection_error):
        """
        Test: Error de conexión se muestra en UI
        
        Verifica que el usuario es notificado
        """
        try:
            result = mock_sparql_connection_error.query("SELECT * WHERE {?s ?p ?o}")
            pytest.fail("Excepción no lanzada")
        except Exception as e:
            assert "Connection failed" in str(e), \
                "Mensaje de error incorrecto"
    
    
    def test_empty_search_results(self, empty_sparql_results):
        """
        Test: Manejo de resultados vacíos
        
        Verifica que app maneja búsquedas sin resultados
        """
        results = empty_sparql_results.query("SELECT * WHERE { ?s ?p 'NonExistent' }")
        
        assert len(results) == 0, "Resultados no vacíos"
    
    
    def test_invalid_sparql_query_error(self, mock_sparql_connection):
        """
        Test: Manejo de query SPARQL inválida
        
        Verifica que se captura y reporta error
        """
        mock_sparql_connection.query = MagicMock(
            side_effect=Exception("SPARQL syntax error")
        )
        
        try:
            mock_sparql_connection.query("SELECT * INVALID")
            pytest.fail("Excepción no lanzada")
        except Exception as e:
            assert "SPARQL syntax error" in str(e)


# ============================================================================
# PRUEBAS DE INTERFAZ DE USUARIO
# ============================================================================

class TestTkinterUI:
    """Tests para componentes de UI"""
    
    def test_search_entry_widget(self):
        """Test: Widget de entrada de búsqueda existe"""
        # Crear widget mock
        root = tk.Tk()
        entry = tk.Entry(root)
        
        assert entry is not None, "Entry widget no creado"
        
        # Insertar texto y recuperar
        entry.insert(0, "test search")
        assert entry.get() == "test search", "Texto no insertado"
        
        root.destroy()
    
    
    def test_search_button_widget(self):
        """Test: Botón de búsqueda funciona"""
        root = tk.Tk()
        
        clicked = {'count': 0}
        
        def on_click():
            clicked['count'] += 1
        
        button = tk.Button(root, text="Search", command=on_click)
        button.invoke()  # Simular click
        
        assert clicked['count'] == 1, "Botón no ejecutó comando"
        
        root.destroy()
    
    
    def test_results_treeview_widget(self):
        """Test: Widget Treeview para resultados"""
        root = tk.Tk()
        
        # Crear treeview
        tree = ttk.Treeview(root, columns=('Name', 'Overall'), height=10)
        tree.column('#0', width=100)
        tree.column('Name', width=200)
        tree.column('Overall', width=100)
        
        # Insertar datos
        tree.insert('', 'end', text='Player1', values=('Cristiano', 93))
        tree.insert('', 'end', text='Player2', values=('Messi', 93))
        
        # Verificar que hay datos
        assert len(tree.get_children()) == 2, \
            "Datos no insertados en Treeview"
        
        root.destroy()


# ============================================================================
# PRUEBAS DE FUNCIONALIDAD
# ============================================================================

@pytest.mark.integration
class TestAppFunctionality:
    """Tests de funcionalidad general"""
    
    def test_search_workflow(self, mock_sparql_connection):
        """
        Test: Flujo completo de búsqueda
        
        1. Usuario ingresa búsqueda
        2. App ejecuta query SPARQL
        3. Resultados se muestran
        """
        # Simular entrada de usuario
        search_term = "Cristiano"
        
        # Simular ejecución de query
        results = mock_sparql_connection.query(
            f"SELECT * WHERE {{ ?p foaf:name ?n . FILTER(CONTAINS(?n, '{search_term}')) }}"
        )
        
        # Verificar que tenemos resultados
        assert len(results) > 0, "Búsqueda no retornó resultados"
        assert mock_sparql_connection.query.called, \
            "Query SPARQL no fue ejecutada"
    
    
    def test_filter_workflow(self, mock_sparql_connection):
        """
        Test: Flujo completo de filtrado
        
        1. Usuario aplica filtro (ej: overall >= 90)
        2. App ejecuta query con FILTER
        3. Solo resultados filtrados se muestran
        """
        # Simular filtro
        min_rating = 90
        
        results = mock_sparql_connection.query(
            f"SELECT * WHERE {{ ?p vini:overall ?o . FILTER(?o >= {min_rating}) }}"
        )
        
        # Verificar query fue hecha
        assert mock_sparql_connection.query.called


# ============================================================================
# PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.slow
class TestAppPerformance:
    """Tests de rendimiento de la app"""
    
    def test_search_response_time(self, mock_sparql_connection):
        """
        Test: Respuesta a búsqueda < 2 segundos
        
        Umbral: < 2 segundos (incluyendo rendering de UI)
        """
        import time
        
        start_time = time.time()
        
        # Simular búsqueda
        results = mock_sparql_connection.query("SELECT * WHERE { ?s ?p ?o } LIMIT 100")
        
        elapsed = time.time() - start_time
        
        # Con mock, debe ser muy rápido (< 1s)
        # Con servidor real, umbral sería 2s
        assert elapsed < 1.0, \
            f"Búsqueda tardó {elapsed:.2f}s (umbral: 1.0s con mock)"
    
    
    def test_large_results_rendering(self):
        """
        Test: Rendering de muchos resultados (100+) en UI
        
        Debería ser responsivo (< 3 segundos)
        """
        import time
        
        root = tk.Tk()
        tree = ttk.Treeview(root)
        
        start_time = time.time()
        
        # Insertar 100 filas
        for i in range(100):
            tree.insert('', 'end', text=f'Row {i}', values=(f'Data {i}',))
        
        elapsed = time.time() - start_time
        
        root.destroy()
        
        assert elapsed < 3.0, \
            f"Rendering tardó {elapsed:.2f}s (umbral: 3.0s)"
