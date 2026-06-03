import pytest

def run_tests(test_files):
    """Función para correr los tests"""
    for test_file in test_files:
        print(f"Ejecutando {test_file}...")
        
        result = pytest.main([test_file])

        if result == 0:
            print(f"{test_file} ejecutado con éxito.")
        else:
            print(f"Error al ejecutar {test_file}.")

if __name__ == '__main__':
    test_files = [
        #'./Aplicacion/Pruebas/test_obtain_data.py',
        #'./Aplicacion/Pruebas/test_normalize_data.py',
        #'./Aplicacion/Pruebas/test_entity_linking.py',
        #'./Aplicacion/Pruebas/test_graph_creation.py',
        './Aplicacion/Pruebas/test_file_upload.py'
    ]

    run_tests(test_files)
