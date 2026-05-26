"""
test_rendimiento_pipeline.py

Pruebas de rendimiento para el pipeline completo del TFG.
Mide tiempos de ejecución de las fases principales y define umbrales.
"""

import pytest
import time
import pandas as pd
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_csv_players(temp_output_dir):
    """Crea CSV de jugadores de prueba"""
    data = {
        'id': range(1, 101),
        'name': [f'Player_{i}' for i in range(1, 101)],
        'overall': [60 + (i % 35) for i in range(100)],
        'age': [20 + (i % 25) for i in range(100)],
    }
    df = pd.DataFrame(data)
    filepath = os.path.join(temp_output_dir, 'players.csv')
    df.to_csv(filepath, index=False)
    return filepath


@pytest.fixture
def sample_csv_teams(temp_output_dir):
    """Crea CSV de equipos de prueba"""
    data = {
        'id': range(1, 21),
        'name': [f'Team_{i}' for i in range(1, 21)],
        'overall': [75 + (i % 20) for i in range(20)],
    }
    df = pd.DataFrame(data)
    filepath = os.path.join(temp_output_dir, 'teams.csv')
    df.to_csv(filepath, index=False)
    return filepath


# ============================================================================
# MEDICIONES DE RENDIMIENTO
# ============================================================================

class TestPipelinePerformance:
    """Tests de rendimiento del pipeline completo"""
    
    def test_csv_loading_performance(self, sample_csv_players):
        """
        Test: Carga de CSV grande (100 filas)
        
        Umbral: < 0.5 segundos
        """
        start_time = time.time()
        
        df = pd.read_csv(sample_csv_players)
        
        elapsed = time.time() - start_time
        
        print(f"\n[PERFORMANCE] CSV loading: {elapsed:.3f}s")
        assert elapsed < 0.5, \
            f"CSV loading tardó {elapsed:.3f}s (umbral: 0.5s)"
        assert len(df) == 100, "CSV no cargado correctamente"
    
    
    def test_dataframe_normalization_performance(self, sample_csv_players):
        """
        Test: Normalización de DataFrame (100 filas)
        
        Umbral: < 0.2 segundos
        """
        df = pd.read_csv(sample_csv_players)
        
        start_time = time.time()
        
        # Simular normalización
        df['name'] = df['name'].str.lower()
        df['overall'] = pd.to_numeric(df['overall'], errors='coerce')
        
        elapsed = time.time() - start_time
        
        print(f"[PERFORMANCE] DataFrame normalization: {elapsed:.3f}s")
        assert elapsed < 0.2, \
            f"Normalización tardó {elapsed:.3f}s (umbral: 0.2s)"
    
    
    def test_deduplication_performance(self, sample_csv_players):
        """
        Test: Deduplicación de 100 registros
        
        Umbral: < 0.1 segundos
        """
        df = pd.read_csv(sample_csv_players)
        
        # Crear duplicados
        df_with_dupes = pd.concat([df, df], ignore_index=True)
        
        start_time = time.time()
        
        df_dedup = df_with_dupes.drop_duplicates().reset_index(drop=True)
        
        elapsed = time.time() - start_time
        
        print(f"[PERFORMANCE] Deduplication: {elapsed:.3f}s")
        assert elapsed < 0.1, \
            f"Deduplicación tardó {elapsed:.3f}s (umbral: 0.1s)"
        assert len(df_dedup) == len(df), "Deduplicación incorrecta"
    
    
    def test_merge_performance(self, sample_csv_players, sample_csv_teams):
        """
        Test: Merge de dos DataFrames (100 players, 20 teams)
        
        Umbral: < 0.5 segundos
        """
        df_players = pd.read_csv(sample_csv_players)
        df_teams = pd.read_csv(sample_csv_teams)
        
        # Crear columna de team para merge
        df_players['team_id'] = df_players['id'] % 20 + 1
        
        start_time = time.time()
        
        df_merged = df_players.merge(df_teams, left_on='team_id', right_on='id', how='left')
        
        elapsed = time.time() - start_time
        
        print(f"[PERFORMANCE] DataFrame merge: {elapsed:.3f}s")
        assert elapsed < 0.5, \
            f"Merge tardó {elapsed:.3f}s (umbral: 0.5s)"
        assert len(df_merged) == len(df_players), "Merge incorrecto"


# ============================================================================
# PRUEBAS DE ESCALABILIDAD
# ============================================================================

@pytest.mark.slow
class TestScalability:
    """Tests de escalabilidad del pipeline"""
    
    def test_csv_loading_1000_rows(self, temp_output_dir):
        """
        Test: Carga de CSV con 1000 filas
        
        Umbral: < 1 segundo
        """
        # Crear CSV grande
        data = {
            'id': range(1, 1001),
            'name': [f'Player_{i}' for i in range(1, 1001)],
            'overall': [60 + (i % 35) for i in range(1000)],
        }
        df = pd.DataFrame(data)
        filepath = os.path.join(temp_output_dir, 'large_players.csv')
        df.to_csv(filepath, index=False)
        
        start_time = time.time()
        
        df_loaded = pd.read_csv(filepath)
        
        elapsed = time.time() - start_time
        
        print(f"\n[SCALABILITY] Loading 1000 rows: {elapsed:.3f}s")
        assert elapsed < 1.0, \
            f"Carga de 1000 filas tardó {elapsed:.3f}s (umbral: 1.0s)"
    
    
    def test_normalization_1000_rows(self, temp_output_dir):
        """
        Test: Normalización de 1000 filas
        
        Umbral: < 1 segundo
        """
        data = {
            'id': range(1, 1001),
            'name': [f'Player_{i}' for i in range(1, 1001)],
        }
        df = pd.DataFrame(data)
        
        start_time = time.time()
        
        df['name'] = df['name'].str.lower()
        
        elapsed = time.time() - start_time
        
        print(f"[SCALABILITY] Normalizing 1000 rows: {elapsed:.3f}s")
        assert elapsed < 1.0, \
            f"Normalización de 1000 filas tardó {elapsed:.3f}s (umbral: 1.0s)"
    
    
    def test_similarity_matching_100_vs_100(self, temp_output_dir):
        """
        Test: Similitud string de 100 vs 100 items (~10k comparaciones)
        
        Umbral: < 5 segundos
        """
        from rapidfuzz import fuzz
        
        # Crear listas para comparar
        items1 = [f'Team_{i}' for i in range(100)]
        items2 = [f'Team_Similar_{i}' for i in range(100)]
        
        start_time = time.time()
        
        # Hacer todas las comparaciones
        scores = []
        for item1 in items1:
            for item2 in items2:
                score = fuzz.ratio(item1, item2)
                scores.append(score)
        
        elapsed = time.time() - start_time
        
        print(f"[SCALABILITY] String similarity 100x100: {elapsed:.3f}s")
        assert elapsed < 5.0, \
            f"Similitud de 100x100 tardó {elapsed:.3f}s (umbral: 5.0s)"
    
    
    def test_ttl_generation_500_entities(self, temp_output_dir):
        """
        Test: Generación de TTL con 500 entidades
        
        Umbral: < 5 segundos
        """
        ttl_lines = [
            "@prefix vini: <http://vini-eii.org/> .",
            "@prefix foaf: <http://xmlns.com/foaf/0.1/> .",
            ""
        ]
        
        start_time = time.time()
        
        # Generar 500 entidades
        for i in range(500):
            ttl_lines.append(f'vini:Player_{i} a vini:Player ;')
            ttl_lines.append(f'  foaf:name "Player {i}" ;')
            ttl_lines.append(f'  vini:overall {60 + (i % 35)} .')
        
        ttl_content = '\n'.join(ttl_lines)
        
        filepath = os.path.join(temp_output_dir, 'large_graph.ttl')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ttl_content)
        
        elapsed = time.time() - start_time
        
        print(f"[SCALABILITY] TTL generation 500 entities: {elapsed:.3f}s")
        assert elapsed < 5.0, \
            f"Generación TTL tardó {elapsed:.3f}s (umbral: 5.0s)"


# ============================================================================
# REPORTES DE RENDIMIENTO
# ============================================================================

class TestPerformanceReport:
    """Tests que generan reportes de rendimiento"""
    
    def test_generate_performance_report(self, temp_output_dir, sample_csv_players, sample_csv_teams):
        """
        Test: Genera reporte de rendimiento del pipeline completo
        
        Mide tiempo de cada fase y reporta resultados
        """
        report = {
            'Phase': [],
            'Operation': [],
            'Time (s)': [],
            'Threshold (s)': [],
            'Status': []
        }
        
        # Fase 1: Carga
        start_time = time.time()
        df_players = pd.read_csv(sample_csv_players)
        phase1_time = time.time() - start_time
        
        report['Phase'].append('Fase 1')
        report['Operation'].append('Data Loading')
        report['Time (s)'].append(f'{phase1_time:.3f}')
        report['Threshold (s)'].append('0.5')
        report['Status'].append('✓ PASS' if phase1_time < 0.5 else '✗ FAIL')
        
        # Fase 2: Normalización
        start_time = time.time()
        df_players['name'] = df_players['name'].str.lower()
        phase2_time = time.time() - start_time
        
        report['Phase'].append('Fase 2')
        report['Operation'].append('Normalization')
        report['Time (s)'].append(f'{phase2_time:.3f}')
        report['Threshold (s)'].append('0.2')
        report['Status'].append('✓ PASS' if phase2_time < 0.2 else '✗ FAIL')
        
        # Fase 3: Deduplicación
        start_time = time.time()
        df_dedup = df_players.drop_duplicates().reset_index(drop=True)
        phase3_time = time.time() - start_time
        
        report['Phase'].append('Fase 3')
        report['Operation'].append('Deduplication')
        report['Time (s)'].append(f'{phase3_time:.3f}')
        report['Threshold (s)'].append('0.1')
        report['Status'].append('✓ PASS' if phase3_time < 0.1 else '✗ FAIL')
        
        # Generar DataFrame de reporte
        df_report = pd.DataFrame(report)
        
        # Guardar reporte
        report_file = os.path.join(temp_output_dir, 'performance_report.csv')
        df_report.to_csv(report_file, index=False)
        
        # Imprimir reporte
        print("\n" + "="*70)
        print("PERFORMANCE REPORT")
        print("="*70)
        print(df_report.to_string(index=False))
        print("="*70)
        
        # Verificar que al menos 50% de tests pasaron
        passed = report['Status'].count('✓ PASS')
        total = len(report['Status'])
        pass_rate = passed / total
        
        assert pass_rate >= 0.5, \
            f"Solo {passed}/{total} tests de rendimiento pasaron"


# ============================================================================
# BENCHMARKING UTILITIES
# ============================================================================

def measure_time(func, *args, **kwargs):
    """Utility para medir tiempo de una función"""
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start_time
    return result, elapsed


class BenchmarkContext:
    """Context manager para benchmarking"""
    
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        print(f"[BENCHMARK] {self.name}: {self.elapsed:.3f}s")


# ============================================================================
# EJEMPLO DE USO DE BENCHMARKING
# ============================================================================

def test_benchmark_example():
    """Test: Ejemplo de uso de BenchmarkContext"""
    
    with BenchmarkContext("CSV loading") as bench:
        # Simular operación
        time.sleep(0.01)  # Simular 10ms
    
    assert bench.elapsed >= 0.01, "Tiempo no medido correctamente"
