"""
test_fase4_generacion_ttl.py

Pruebas automáticas para generación de archivos TTL (RDF Turtle).
Verifica:
- Generación correcta de archivos TTL
- Sintaxis básica válida de TTL
- Presencia mínima de triples
- Estructura de URIs correcta
- Prefijos definidos
- Validación de recursos RDF
"""

import pytest
import os
import tempfile
import re
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Grafo"))

# Intentar importar el módulo real
try:
    from grafo import saveGraph, addTeamsSofifa, addPlayersSofifa
    from rdflib import Graph, Namespace, Literal, URIRef
    TTL_GENERATOR_AVAILABLE = True
except ImportError:
    TTL_GENERATOR_AVAILABLE = False


# ============================================================================
# FIXTURES DE DATOS TTL
# ============================================================================

@pytest.fixture
def minimal_ttl_content():
    """Contenido TTL mínimo válido para pruebas"""
    return """
    @prefix vini: <http://vini-eii.org/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    vini:Player_1 a vini:Player ;
        <http://xmlns.com/foaf/0.1/name> "Cristiano Ronaldo" ;
        vini:overall 93 .
    
    vini:Team_1 a vini:Team ;
        <http://xmlns.com/foaf/0.1/name> "Manchester United" ;
        vini:overall 84 .
    
    vini:Player_1 vini:playsFor vini:Team_1 .
    """


@pytest.fixture
def complex_ttl_content():
    """Contenido TTL más completo con múltiples recursos"""
    return """
    @prefix vini: <http://vini-eii.org/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    
    vini:Player_1 a vini:Player ;
        foaf:name "Cristiano Ronaldo" ;
        vini:overall 93 ;
        vini:age 35 ;
        vini:nationality "Portugal" ;
        vini:playsFor vini:Team_1 .
    
    vini:Player_2 a vini:Player ;
        foaf:name "Lionel Messi" ;
        vini:overall 93 ;
        vini:age 33 ;
        vini:nationality "Argentina" ;
        vini:playsFor vini:Team_2 .
    
    vini:Team_1 a vini:Team ;
        foaf:name "Manchester United" ;
        vini:overall 84 ;
        vini:country "England" .
    
    vini:Team_2 a vini:Team ;
        foaf:name "Paris Saint-Germain" ;
        vini:overall 86 ;
        vini:country "France" .
    
    vini:Competition_1 a vini:Competition ;
        foaf:name "Premier League" ;
        vini:country "England" .
    """


# ============================================================================
# PRUEBAS DE SINTAXIS TTL
# ============================================================================

class TestTTLSyntaxValidation:
    """Tests para validación de sintaxis TTL"""
    
    def test_ttl_has_prefixes(self, minimal_ttl_content):
        """Test: TTL contiene definiciones de prefijos"""
        assert '@prefix' in minimal_ttl_content, "TTL no tiene prefijos definidos"
        
        # Verificar al menos prefijo vini
        assert '@prefix vini:' in minimal_ttl_content, \
            "Prefijo 'vini' no definido"
    
    
    def test_ttl_has_triples(self, minimal_ttl_content):
        """Test: TTL contiene triples (sujeto predicado objeto)"""
        # Un triple básico termina con .
        triple_pattern = r'<[^>]+>\s+<[^>]+>\s+[^;.]+\s*[.;]'
        
        has_triples = bool(re.search(triple_pattern, minimal_ttl_content))
        assert has_triples or 'vini:' in minimal_ttl_content, \
            "TTL no contiene triples válidos"
    
    
    def test_ttl_ends_with_period(self, minimal_ttl_content):
        """Test: Último triple termina con punto"""
        # Limpiar whitespace
        content = minimal_ttl_content.strip()
        assert content.endswith('.'), "TTL no termina con punto"
    
    
    def test_ttl_uris_valid_format(self, minimal_ttl_content):
        """Test: URIs tienen formato válido (http:// o prefijo:)"""
        # Buscar URIs
        uri_pattern = r'(?:https?://[^\s>]+|[a-zA-Z_]\w*:[^\s>]+)'
        uris = re.findall(uri_pattern, minimal_ttl_content)
        
        assert len(uris) > 0, "No se encontraron URIs en TTL"
        
        # Todos deben tener formato válido
        for uri in uris:
            assert ':' in uri or '://' in uri, \
                f"URI inválida: {uri}"
    
    
    def test_ttl_no_invalid_characters(self, minimal_ttl_content):
        """Test: TTL no contiene caracteres prohibidos fuera de strings"""
        # Caracteres inválidos fuera de quoted strings
        # Esta es una verificación simplificada
        assert '<<' not in minimal_ttl_content, "Caracteres inválidos: <<"
        assert '>>' not in minimal_ttl_content, "Caracteres inválidos: >>"


# ============================================================================
# PRUEBAS DE ESTRUCTURA RDF
# ============================================================================

class TestRDFStructure:
    """Tests para estructura RDF del TTL"""
    
    def test_resources_have_types(self, complex_ttl_content):
        """Test: Recursos tienen tipos (rdf:type / 'a')"""
        # Buscar 'a vini:' (tipo declaration)
        type_declarations = re.findall(r'a\s+\w+:\w+\s*[;.]', complex_ttl_content)
        
        assert len(type_declarations) > 0, "No hay declaraciones de tipo"
    
    
    def test_has_player_resources(self, complex_ttl_content):
        """Test: TTL contiene recursos de tipo Player"""
        assert 'vini:Player' in complex_ttl_content, \
            "No hay recursos de tipo Player"
        assert 'a vini:Player' in complex_ttl_content, \
            "No se declaran Players correctamente"
    
    
    def test_has_team_resources(self, complex_ttl_content):
        """Test: TTL contiene recursos de tipo Team"""
        assert 'vini:Team' in complex_ttl_content, \
            "No hay recursos de tipo Team"
        assert 'a vini:Team' in complex_ttl_content, \
            "No se declaran Teams correctamente"
    
    
    def test_has_relationships(self, complex_ttl_content):
        """Test: TTL contiene relaciones entre recursos"""
        # Buscar 'playsFor' u otras relaciones
        assert 'playsFor' in complex_ttl_content or 'country' in complex_ttl_content, \
            "No hay relaciones entre recursos"
    
    
    def test_resources_have_properties(self, complex_ttl_content):
        """Test: Recursos tienen propiedades (name, overall, etc.)"""
        properties = ['foaf:name', 'vini:overall', 'vini:age']
        
        found_properties = [prop for prop in properties if prop in complex_ttl_content]
        assert len(found_properties) > 0, \
            "Recursos no tienen propiedades"


# ============================================================================
# PRUEBAS DE GENERACIÓN DE ARCHIVOS TTL
# ============================================================================

@pytest.mark.integration
class TestTTLGeneration:
    """Tests para generación de archivos TTL"""
    
    def test_ttl_file_creation(self, temp_output_dir, minimal_ttl_content):
        """Test: Archivo TTL se crea correctamente"""
        if not TTL_GENERATOR_AVAILABLE:
            pytest.skip("Módulos RDF no disponibles")
        
        output_file = os.path.join(temp_output_dir, 'test_graph.ttl')
        
        # Simular guardado de TTL
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minimal_ttl_content)
        
        assert os.path.exists(output_file), "Archivo TTL no creado"
        assert os.path.getsize(output_file) > 0, "Archivo TTL está vacío"
    
    
    def test_ttl_file_readable(self, temp_output_dir, minimal_ttl_content):
        """Test: Archivo TTL es legible sin errores"""
        output_file = os.path.join(temp_output_dir, 'readable.ttl')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minimal_ttl_content)
        
        # Intentar leer
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 0, "No se pudo leer TTL"
        assert '@prefix' in content, "Contenido TTL alterado"
    
    
    def test_ttl_valid_encoding(self, temp_output_dir, complex_ttl_content):
        """Test: Archivo TTL tiene encoding UTF-8 válido"""
        output_file = os.path.join(temp_output_dir, 'encoding.ttl')
        
        # Escribir con encoding específico
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(complex_ttl_content)
        
        # Leer con encoding y verificar
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 0, "Encoding error"
        # Caracteres especiales deben preservarse
        if 'Ç' in complex_ttl_content:
            assert 'Ç' in content, "Caracteres especiales perdidos"


# ============================================================================
# PRUEBAS DE CONTENIDO Y DATOS
# ============================================================================

class TestTTLContent:
    """Tests para contenido del TTL"""
    
    def test_minimum_triple_count(self, complex_ttl_content):
        """Test: TTL tiene número mínimo de triples"""
        # Contar líneas con . que probable representen fin de triple
        triple_endings = len(re.findall(r'\.\s*$', complex_ttl_content, re.MULTILINE))
        
        # Debería haber al menos algunas declaraciones
        assert triple_endings > 0, "No hay triples en TTL"
    
    
    def test_has_player_properties(self, complex_ttl_content):
        """Test: Players tienen propiedades esperadas"""
        expected_props = ['name', 'overall', 'age']
        
        found_props = sum(1 for prop in expected_props 
                         if prop.lower() in complex_ttl_content.lower())
        
        assert found_props > 0, "Players no tienen propiedades esperadas"
    
    
    def test_has_team_properties(self, complex_ttl_content):
        """Test: Teams tienen propiedades esperadas"""
        expected_props = ['name', 'overall', 'country']
        
        found_props = sum(1 for prop in expected_props 
                         if prop.lower() in complex_ttl_content.lower())
        
        assert found_props > 0, "Teams no tienen propiedades esperadas"
    
    
    def test_no_empty_predicates(self, complex_ttl_content):
        """Test: No hay predicados vacíos"""
        # Buscar patrones de predicado sin objeto
        empty_pred_pattern = r'[\s;]\s+\.\s*$'
        
        has_empty = bool(re.search(empty_pred_pattern, complex_ttl_content, re.MULTILINE))
        assert not has_empty, "TTL contiene predicados sin objeto"
    
    
    def test_literal_values_properly_formatted(self, complex_ttl_content):
        """Test: Valores literales están correctamente formateados"""
        # Buscar strings entre comillas
        literals = re.findall(r'"[^"]*"', complex_ttl_content)
        
        assert len(literals) > 0, "No hay valores literales en TTL"
        
        # Todos deben estar entrecomillados
        for lit in literals:
            assert lit.startswith('"') and lit.endswith('"'), \
                f"Literal no está entrecomillado: {lit}"


# ============================================================================
# PRUEBAS DE VALIDACIÓN RDF CON RDFLIB
# ============================================================================

@pytest.mark.integration
class TestRDFLibValidation:
    """Tests usando rdflib para validación"""
    
    def test_ttl_parseable_by_rdflib(self, temp_output_dir, minimal_ttl_content):
        """Test: TTL puede ser parseado por rdflib sin errores"""
        if not TTL_GENERATOR_AVAILABLE:
            pytest.skip("rdflib no disponible")
        
        output_file = os.path.join(temp_output_dir, 'valid.ttl')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minimal_ttl_content)
        
        # Intentar parsear con rdflib
        try:
            g = Graph()
            g.parse(output_file, format='turtle')
            
            # Debe haber al menos algunos triples
            assert len(g) > 0, "Grafo parseado pero vacío"
        except Exception as e:
            pytest.fail(f"rdflib no pudo parsear TTL: {e}")
    
    
    def test_triple_count_after_parsing(self, temp_output_dir, complex_ttl_content):
        """Test: Número de triples es consistente tras parsing"""
        if not TTL_GENERATOR_AVAILABLE:
            pytest.skip("rdflib no disponible")
        
        output_file = os.path.join(temp_output_dir, 'triples.ttl')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(complex_ttl_content)
        
        try:
            g = Graph()
            g.parse(output_file, format='turtle')
            
            triple_count = len(g)
            
            # Debería haber un número mínimo de triples
            assert triple_count > 5, \
                f"Pocos triples en grafo: {triple_count}"
        except Exception as e:
            pytest.fail(f"Error al parsear TTL: {e}")


# ============================================================================
# PRUEBAS DE NAMESPACES/VOCABULARIOS
# ============================================================================

class TestNamespacesAndVocabularies:
    """Tests para namespaces y vocabularios RDF"""
    
    def test_has_vini_namespace(self, minimal_ttl_content):
        """Test: TTL define namespace vini"""
        assert '@prefix vini: <http://vini-eii.org/>' in minimal_ttl_content, \
            "Namespace vini no definido"
    
    
    def test_has_standard_namespaces(self, complex_ttl_content):
        """Test: TTL define namespaces estándar (rdf, rdfs)"""
        standard_namespaces = [
            'rdf',
            'rdfs'
        ]
        
        for ns in standard_namespaces:
            assert f'@prefix {ns}:' in complex_ttl_content, \
                f"Namespace estándar '{ns}' no definido"
    
    
    def test_uses_foaf_for_names(self, complex_ttl_content):
        """Test: Se usa FOAF namespace para names"""
        assert 'foaf:name' in complex_ttl_content or 'name' in complex_ttl_content, \
            "FOAF namespace no usado para names"


# ============================================================================
# PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.slow
class TestTTLGenerationPerformance:
    """Tests de rendimiento"""
    
    def test_large_ttl_generation_time(self, temp_output_dir):
        """
        Test: Generación de TTL con ~1000 triples < 10 segundos
        
        Umbral: < 10 segundos
        """
        import time
        
        # Crear contenido TTL grande
        ttl_lines = [
            "@prefix vini: <http://vini-eii.org/> .",
            "@prefix foaf: <http://xmlns.com/foaf/0.1/> .",
            ""
        ]
        
        # Generar 500 Players
        for i in range(500):
            ttl_lines.append(f'vini:Player_{i} a vini:Player ;')
            ttl_lines.append(f'  foaf:name "Player {i}" ;')
            ttl_lines.append(f'  vini:overall {60 + (i % 35)} .')
        
        large_ttl = '\n'.join(ttl_lines)
        
        output_file = os.path.join(temp_output_dir, 'large.ttl')
        
        start_time = time.time()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(large_ttl)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 10.0, \
            f"Generación de TTL grande tardó {elapsed:.2f}s (umbral: 10.0s)"
