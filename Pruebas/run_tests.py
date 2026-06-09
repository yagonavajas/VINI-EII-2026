import os
import pytest

def run_tests(test_files):
    """Función para correr los tests"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for test_file in test_files:
        test_path = os.path.join(script_dir, test_file)

        print(f"Ejecutando {test_path}...")
        
        result = pytest.main([test_path])

        if result == 0:
            print(f"{test_file} ejecutado con éxito.")
        else:
            print(f"Error al ejecutar {test_file}.")

if __name__ == '__main__':
    test_files = [
        'test_obtain_data.py',
        'test_normalize_data.py',
        'test_entity_linking.py',
        'test_graph.py',
        'test_app.py'
    ]

    run_tests(test_files)
