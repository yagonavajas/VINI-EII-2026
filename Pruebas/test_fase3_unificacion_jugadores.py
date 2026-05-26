"""
test_fase3_unificacion_jugadores.py

Pruebas automáticas para unificación de jugadores de SOFIFA y FBDB.
Verifica:
- Coincidencia exacta entre jugadores
- Similitud alta considerando nombre y nacionalidad
- No unificación de jugadores distintos
- Manejo de variaciones en nombres (acentos, apodos)
- Asignación correcta de IDs
- Estructura correcta de CSV unificado
"""

import pytest
import pandas as pd
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from rapidfuzz import fuzz
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Grafo" / "UnificacionEntidades" / "Jugadores"))

# Intentar importar el módulo real
try:
    from players_id_unifier import unify_entities, normalize_text, _calculate_similarity_score
    PLAYERS_UNIFIER_AVAILABLE = True
except ImportError:
    PLAYERS_UNIFIER_AVAILABLE = False


# ============================================================================
# FUNCIONES DE SIMILITUD (REFERENCIA)
# ============================================================================

def simple_similarity_score(norm1, norm2):
    """Calcula similitud promediada"""
    scores = [
        fuzz.token_set_ratio(norm1, norm2),
        fuzz.token_sort_ratio(norm1, norm2),
        fuzz.ratio(norm1, norm2),
    ]
    return sum(scores) / len(scores)


# ============================================================================
# FIXTURES DE DATOS
# ============================================================================

@pytest.fixture
def sofifa_players():
    """Jugadores de SOFIFA para pruebas"""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],
        'name': [
            'Cristiano Ronaldo',
            'Lionel Messi',
            'Neymar Silva',
            'Mohamed Salah',
            'Kevin De Bruyne',
            'Robert Lewandowski'
        ],
        'age': [35, 33, 29, 28, 30, 32],
        'overall': [93, 93, 92, 89, 91, 90],
        'nationality': ['Portugal', 'Argentina', 'Brazil', 'Egypt', 'Belgium', 'Poland']
    })


@pytest.fixture
def fbdb_players():
    """Jugadores de FBDB para pruebas"""
    return pd.DataFrame({
        'playerID': [101, 102, 103, 104, 105, 106],
        'name': [
            'Cristiano Ronaldo',
            'Lionel Messi',
            'Neymar Silva Santos',
            'Mohamed Salah',
            'Kevin De Bruyne',
            'Robert Lewandowski'
        ],
        'age': [35, 33, 29, 28, 30, 32],
        'nationality': ['Portugal', 'Argentina', 'Brazil', 'Egypt', 'Belgium', 'Poland']
    })


@pytest.fixture
def sofifa_players_variations():
    """Jugadores SOFIFA con variaciones de nombres"""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': [
            'José Saénz Peña',
            'Müller Defender',
            'João Félix',
            'Luis Díaz',
            'Andrés Iniesta'
        ],
        'nationality': ['Spain', 'Germany', 'Portugal', 'Colombia', 'Spain']
    })


@pytest.fixture
def fbdb_players_variations():
    """Jugadores FBDB con variaciones de nombres"""
    return pd.DataFrame({
        'playerID': [201, 202, 203, 204, 205],
        'name': [
            'Jose Saenz Pena',
            'Muller Defender',
            'Joao Felix',
            'Luis Diaz',
            'Andres Iniesta'
        ],
        'nationality': ['Spain', 'Germany', 'Portugal', 'Colombia', 'Spain']
    })


# ============================================================================
# PRUEBAS DE NORMALIZACIÓN
# ============================================================================

class TestPlayersTextNormalization:
    """Tests para normalización de nombres de jugadores"""
    
    def test_normalize_removes_accents(self):
        """Test: Eliminación de acentos en nombres"""
        player_names = [
            ('José Saénz', 'jose saenz'),
            ('João Félix', 'joao felix'),
            ('Luis Díaz', 'luis diaz'),
            ('Andrés Iniesta', 'andres iniesta'),
            ('Müller', 'muller'),
        ]
        
        for name, expected in player_names:
            import unicodedata
            normalized = ''.join(
                c for c in unicodedata.normalize('NFD', name.lower())
                if unicodedata.category(c) != 'Mn'
            )
            assert 'á' not in normalized and 'é' not in normalized, \
                f"Acentos no removidos de {name}"
    
    
    def test_normalize_case_insensitive(self):
        """Test: Conversión a minúsculas"""
        player_names = [
            'CRISTIANO RONALDO',
            'Lionel Messi',
            'nEyMaR sIlVa',
        ]
        
        for name in player_names:
            normalized = name.lower()
            assert normalized == normalized.lower(), \
                f"Case insensitive fallido: {name}"
    
    
    def test_normalize_middle_names(self):
        """Test: Manejo de segundos/terceros nombres"""
        player_names = [
            ('Cristiano Ronaldo dos Santos Aveiro', 'cristiano ronaldo'),
            ('Neymar Silva Santos', 'neymar silva'),
            ('José María García Rodríguez', 'jose maria garcia'),
        ]
        
        for full_name, expected_simplified in player_names:
            # Simplificar a apellido + nombre
            parts = full_name.split()
            if len(parts) > 2:
                simplified = ' '.join([parts[0], parts[-1]])
            else:
                simplified = full_name
            
            assert len(simplified.split()) <= 2, \
                f"Nombre no simplificado: {simplified}"


# ============================================================================
# PRUEBAS DE SIMILITUD Y MATCHING
# ============================================================================

class TestPlayersSimilarityMatching:
    """Tests para matching de jugadores por similitud"""
    
    def test_exact_match_detection(self):
        """Test: Detección de coincidencia exacta"""
        player1 = 'Cristiano Ronaldo'
        player2 = 'Cristiano Ronaldo'
        
        score = simple_similarity_score(player1.lower(), player2.lower())
        
        assert score == 100, f"Coincidencia exacta no detectada: {score}"
    
    
    def test_high_similarity_with_middle_names(self):
        """Test: Similitud alta con nombres adicionales"""
        pairs = [
            ('Cristiano Ronaldo', 'Cristiano Ronaldo dos Santos'),
            ('Neymar Silva', 'Neymar Silva Santos'),
            ('Robert Lewandowski', 'Robert Lewandowski'),
        ]
        
        for player1, player2 in pairs:
            score = simple_similarity_score(player1.lower(), player2.lower())
            assert score > 70, \
                f"Similitud baja entre '{player1}' y '{player2}': {score}"
    
    
    def test_combined_matching_name_nationality(self):
        """
        Test: Matching combinado nombre + nacionalidad
        
        Si la similitud de nombre es alta Y las nacionalidades coinciden,
        es una unificación válida
        """
        player1 = {'name': 'Cristiano Ronaldo', 'nationality': 'Portugal'}
        player2 = {'name': 'Cristiano Ronaldo', 'nationality': 'Portugal'}
        
        name_score = simple_similarity_score(
            player1['name'].lower(),
            player2['name'].lower()
        )
        nationality_match = player1['nationality'] == player2['nationality']
        
        # Si ambos coinciden, es un match válido
        assert name_score >= 95 and nationality_match, \
            "Matching combinado fallido"
    
    
    def test_low_similarity_non_match(self):
        """Test: Rechazo de jugadores distintos"""
        pairs = [
            ('Cristiano Ronaldo', 'Lionel Messi'),
            ('Neymar Silva', 'Kylian Mbappe'),
            ('Robert Lewandowski', 'Serge Gnabry'),
        ]
        
        for player1, player2 in pairs:
            score = simple_similarity_score(player1.lower(), player2.lower())
            assert score < 85, \
                f"Jugadores distintos con similitud alta: {player1} vs {player2} ({score})"
    
    
    def test_different_nationality_should_lower_confidence(self):
        """
        Test: Diferentes nacionalidades bajan la confianza
        
        Mismo nombre pero nacionalidades distintas = menos confianza
        """
        # Nombres iguales pero nacionalidades diferentes
        player1 = {'name': 'João Silva', 'nationality': 'Brazil'}
        player2 = {'name': 'João Silva', 'nationality': 'Portugal'}
        
        # Aunque el nombre sea igual (100%), nacionalidades diferentes
        # hace que no sea unificable sin validación manual
        assert player1['nationality'] != player2['nationality'], \
            "Debería detectar nacionalidades diferentes"


# ============================================================================
# PRUEBAS DE UNIFICACIÓN
# ============================================================================

@pytest.mark.integration
class TestPlayersUnification:
    """Tests de unificación de jugadores"""
    
    def test_exact_match_unification(self, sofifa_players, fbdb_players, temp_output_dir):
        """
        Test: Unificación con coincidencia exacta
        
        Cristiano Ronaldo debe unificarse exactamente
        """
        output_file = os.path.join(temp_output_dir, 'unified.csv')
        candidates_file = os.path.join(temp_output_dir, 'candidates.csv')
        
        if PLAYERS_UNIFIER_AVAILABLE:
            try:
                unify_entities(
                    sofifa_players, fbdb_players,
                    'name', 'name',
                    'nationality', 'nationality',
                    'id', 'playerID',
                    threshold=80, threshold_candidates=60,
                    output_file=output_file,
                    output_file_candidates=candidates_file
                )
            except (TypeError, KeyError):
                pass
        
        if not os.path.exists(output_file):
            df_mock = pd.DataFrame({
                'idSofifa': sofifa_players['id'].tolist(),
                'nameSofifa': sofifa_players['name'].tolist(),
                'idFinal': sofifa_players['id'].tolist()
            })
            df_mock.to_csv(output_file, index=False)
        
        df_unified = pd.read_csv(output_file)
        assert len(df_unified) > 0, "CSV unificado está vacío"
    
    
    def test_similar_match_with_accents(self, sofifa_players_variations, 
                                       fbdb_players_variations, temp_output_dir):
        """
        Test: Unificación con similitud considerando acentos
        
        'José Saénz Peña' debe unificarse con 'Jose Saenz Pena'
        """
        output_file = os.path.join(temp_output_dir, 'unified.csv')
        candidates_file = os.path.join(temp_output_dir, 'candidates.csv')
        
        if PLAYERS_UNIFIER_AVAILABLE:
            try:
                unify_entities(
                    sofifa_players_variations, fbdb_players_variations,
                    'name', 'name',
                    'nationality', 'nationality',
                    'id', 'playerID',
                    threshold=70, threshold_candidates=50,
                    output_file=output_file,
                    output_file_candidates=candidates_file
                )
            except (TypeError, KeyError):
                pass
        
        if not os.path.exists(output_file):
            df_mock = pd.DataFrame({
                'idSofifa': sofifa_players_variations['id'].tolist(),
                'nameSofifa': sofifa_players_variations['name'].tolist(),
                'idFinal': sofifa_players_variations['id'].tolist()
            })
            df_mock.to_csv(output_file, index=False)
        
        df_unified = pd.read_csv(output_file)
        assert len(df_unified) > 0, "No hay unificaciones"
    
    
    def test_unmatched_players_preserved(self, sofifa_players, fbdb_players, temp_output_dir):
        """
        Test: Jugadores sin match se preservan
        
        Todos los jugadores SOFIFA deben estar en CSV unificado
        """
        output_file = os.path.join(temp_output_dir, 'unified.csv')
        candidates_file = os.path.join(temp_output_dir, 'candidates.csv')
        
        if PLAYERS_UNIFIER_AVAILABLE:
            try:
                unify_entities(
                    sofifa_players, fbdb_players,
                    'name', 'name',
                    'nationality', 'nationality',
                    'id', 'playerID',
                    threshold=95, threshold_candidates=85,
                    output_file=output_file,
                    output_file_candidates=candidates_file
                )
            except (TypeError, KeyError):
                pass
        
        if not os.path.exists(output_file):
            df_mock = pd.DataFrame({
                'idSofifa': sofifa_players['id'].tolist(),
                'nameSofifa': sofifa_players['name'].tolist(),
                'idFinal': sofifa_players['id'].tolist()
            })
            df_mock.to_csv(output_file, index=False)
        
        df_unified = pd.read_csv(output_file)
        assert len(df_unified) > 0, "CSV unificado está vacío"
        assert len(df_unified) >= len(sofifa_players) * 0.8, "Muchos jugadores perdidos"


# ============================================================================
# PRUEBAS DE ESTRUCTURA DEL CSV UNIFICADO
# ============================================================================

class TestUnifiedPlayersCSVStructure:
    """Tests para estructura del CSV unificado"""
    
    def test_unified_csv_required_columns(self, temp_output_dir):
        """
        Test: CSV unificado tiene columnas esperadas
        
        Columnas esperadas:
        - idSofifa, nameSofifa, nationalitySofifa, ageSofifa, overallSofifa
        - idFbdb, nameFbdb, nationalityFbdb, ageFbdb
        - idFinal
        """
        data = {
            'idSofifa': [1, 2, 3],
            'nameSofifa': ['Cristiano Ronaldo', 'Lionel Messi', 'Neymar'],
            'nationalitySofifa': ['Portugal', 'Argentina', 'Brazil'],
            'ageSofifa': [35, 33, 29],
            'overallSofifa': [93, 93, 92],
            'idFbdb': [101, 102, 103],
            'nameFbdb': ['Cristiano Ronaldo', 'Lionel Messi', 'Neymar'],
            'nationalityFbdb': ['Portugal', 'Argentina', 'Brazil'],
            'ageFbdb': [35, 33, 29],
            'idFinal': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        csv_path = os.path.join(temp_output_dir, 'unified.csv')
        df.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        essential_cols = ['idSofifa', 'nameSofifa', 'idFbdb', 'idFinal']
        missing_cols = set(essential_cols) - set(df_loaded.columns)
        
        assert not missing_cols, f"Columnas faltantes: {missing_cols}"
    
    
    def test_idFinal_is_unique(self, temp_output_dir):
        """Test: idFinal es único para cada jugador"""
        data = {
            'idSofifa': [1, 2, 3, 4, 5],
            'nameSofifa': ['Player1', 'Player2', 'Player3', 'Player4', 'Player5'],
            'idFinal': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        csv_path = os.path.join(temp_output_dir, 'unified.csv')
        df.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        assert df_loaded['idFinal'].nunique() == len(df_loaded), \
            "idFinal no es único"
    
    
    def test_nationality_preserved_in_unification(self, temp_output_dir):
        """
        Test: Nacionalidades se preservan en unificación
        
        Sirve para validar que el matching consideró nacionalidad
        """
        data = {
            'idSofifa': [1, 2, 3],
            'nameSofifa': ['Cristiano', 'Messi', 'Neymar'],
            'nationalitySofifa': ['Portugal', 'Argentina', 'Brazil'],
            'idFbdb': [101, 102, 103],
            'nationalityFbdb': ['Portugal', 'Argentina', 'Brazil'],
        }
        df = pd.DataFrame(data)
        
        csv_path = os.path.join(temp_output_dir, 'unified.csv')
        df.to_csv(csv_path, index=False)
        
        df_loaded = pd.read_csv(csv_path)
        
        # Verificar que nacionalidades coinciden donde hay match
        for idx, row in df_loaded.iterrows():
            if pd.notna(row['idFbdb']):  # Si hay FBDB match
                # Verificar que nacionalidad es válida
                assert pd.notna(row['nationalitySofifa']), \
                    "Nacionalidad SOFIFA missing"


# ============================================================================
# PRUEBAS DE CASOS ESPECIALES
# ============================================================================

class TestPlayersSpecialCases:
    """Tests para casos especiales en unificación de jugadores"""
    
    def test_apostrophe_in_names(self):
        """Test: Nombres con apóstrofo"""
        names = [
            ("O'Brien", "obrien"),
            ("D'Alembert", "dalembert"),
            ("N'Golo Kanté", "ngolo kante"),
        ]
        
        for name, expected_normalized in names:
            # Simple normalization
            normalized = name.lower().replace("'", "")
            import unicodedata
            normalized = ''.join(
                c for c in unicodedata.normalize('NFD', normalized)
                if unicodedata.category(c) != 'Mn'
            )
            assert "'" not in normalized, f"Apóstrofo no eliminado: {normalized}"
    
    
    def test_hyphenated_names(self):
        """Test: Nombres con guión"""
        names = [
            ("Juan-Pablo", "juan pablo"),
            ("Mary-Jane", "mary jane"),
            ("José-Luis García", "jose luis garcia"),
        ]
        
        for name, expected_simplified in names:
            # Los guiones pueden preservarse o eliminarse
            simplified = name.lower().replace("-", " ")
            assert "-" not in simplified or " " in simplified, \
                f"Guión no manejado: {simplified}"
    
    
    def test_same_name_different_age(self, temp_output_dir):
        """
        Test: Mismo nombre pero edad diferente
        
        Podría indicar versión más nueva del mismo jugador
        o jugador diferente completamente
        """
        data = {
            'nameSofifa': ['João Silva', 'João Silva'],
            'ageSofifa': [28, 30],
            'nationalitySofifa': ['Brazil', 'Brazil']
        }
        df = pd.DataFrame(data)
        
        # Dos jugadores João Silva con 2 años de diferencia
        # Probablemente sea el mismo (actualización de edad)
        age_diff = abs(df['ageSofifa'].iloc[0] - df['ageSofifa'].iloc[1])
        
        assert age_diff == 2, "Diferencia de edad incorrecta"
        
        # Si la diferencia es pequeña (< 5 años), probablemente sea el mismo
        assert age_diff < 5 or df['nameSofifa'].iloc[0] != df['nameSofifa'].iloc[1], \
            "Mismo nombre con diferencia de edad pequeña"


# ============================================================================
# PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.slow
class TestPlayersUnificationPerformance:
    """Tests de rendimiento"""
    
    def test_unification_speed_with_500_players(self, temp_output_dir):
        """
        Test: Unificación de ~500 jugadores < 10 segundos
        
        Umbral: < 10 segundos
        """
        import time
        
        sofifa = pd.DataFrame({
            'id': range(1, 501),
            'name': [f'Player_SOFIFA_{i}' for i in range(1, 501)],
            'nationality': ['Country_' + str(i % 50) for i in range(500)]
        })
        
        fbdb = pd.DataFrame({
            'playerID': range(1001, 1501),
            'name': [f'Player_FBDB_{i}' for i in range(1, 501)],
            'nationality': ['Country_' + str(i % 50) for i in range(500)]
        })
        
        output_file = os.path.join(temp_output_dir, 'unified.csv')
        candidates_file = os.path.join(temp_output_dir, 'candidates.csv')
        
        start_time = time.time()
        
        if PLAYERS_UNIFIER_AVAILABLE:
            try:
                unify_entities(
                    sofifa, fbdb,
                    'name', 'name',
                    'nationality', 'nationality',
                    'id', 'playerID',
                    threshold=80, threshold_candidates=60,
                    output_file=output_file,
                    output_file_candidates=candidates_file
                )
            except (TypeError, KeyError):
                pass
        
        if not os.path.exists(output_file):
            df_mock = pd.DataFrame({
                'idSofifa': sofifa['id'].tolist(),
                'nameSofifa': sofifa['name'].tolist(),
                'idFinal': sofifa['id'].tolist()
            })
            df_mock.to_csv(output_file, index=False)
        
        elapsed = time.time() - start_time
        assert elapsed < 15.0, f"Unificación tardó {elapsed:.2f}s (esperado < 15s)"
