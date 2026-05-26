"""
run_tests.py - Script para ejecutar tests con opciones convenientes

Uso:
    python run_tests.py                  # Ejecutar todos los tests
    python run_tests.py --fase 1         # Ejecutar solo Fase 1
    python run_tests.py --report html    # Generar reporte HTML
    python run_tests.py --performance    # Solo tests de rendimiento
    python run_tests.py --quick          # Solo tests rápidos (no --slow)
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse


# Rutas
PROJECT_ROOT = Path(__file__).parent
PRUEBAS_DIR = PROJECT_ROOT  # run_tests.py ya está en el directorio Pruebas
TEST_FILES = {
    1: [
        "test_fase1_descarga_kaggle.py",
        "test_fase1_descarga_wikidata.py",
        "test_fase1_descarga_scraping.py"
    ],
    2: ["test_fase2_normalizacion.py"],
    3: [
        "test_fase3_unificacion_equipos.py",
        "test_fase3_unificacion_jugadores.py",
        "test_fase3_unificacion_paises.py",
    ],
    4: ["test_fase4_generacion_ttl.py"],
    5: ["test_fase5_fuseki_carga.py"],
    6: ["test_fase6_app_tkinter.py"],
    "performance": ["test_rendimiento_pipeline.py"]
}


def run_pytest(args):
    """Ejecuta pytest con argumentos"""
    cmd = [sys.executable, "-m", "pytest"] + args
    print(f"\n{'='*70}")
    print(f"Ejecutando: {' '.join(cmd)}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, cwd=str(PRUEBAS_DIR))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tests del TFG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_tests.py --all              Ejecutar todos los tests
  python run_tests.py --fase 1           Ejecutar solo Fase 1
  python run_tests.py --fase 3           Ejecutar solo Fase 3
  python run_tests.py --quick            Ejecutar tests rápidos
  python run_tests.py --performance      Ejecutar solo tests de rendimiento
  python run_tests.py --report html      Generar reporte HTML
  python run_tests.py --coverage         Mostrar cobertura de código
  python run_tests.py --integration      Solo tests de integración
  python run_tests.py --unit             Solo tests unitarios
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los tests")
    parser.add_argument("--fase", type=int, choices=[1, 2, 3, 4, 5, 6], 
                       help="Ejecutar tests de fase específica")
    parser.add_argument("--performance", action="store_true", 
                       help="Ejecutar solo tests de rendimiento")
    parser.add_argument("--quick", action="store_true", 
                       help="Ejecutar solo tests rápidos (excluir --slow)")
    parser.add_argument("--report", choices=["html", "junit"], 
                       help="Generar reporte en formato especificado")
    parser.add_argument("--coverage", action="store_true", 
                       help="Mostrar cobertura de código")
    parser.add_argument("--integration", action="store_true", 
                       help="Ejecutar solo tests de integración")
    parser.add_argument("--unit", action="store_true", 
                       help="Ejecutar solo tests unitarios (exluir integration)")
    parser.add_argument("--markers", type=str, 
                       help="Ejecutar tests con marker específico")
    parser.add_argument("--verbose", "-v", action="count", default=1, 
                       help="Aumentar verbosidad (usar múltiples veces)")
    parser.add_argument("--failfast", "-x", action="store_true", 
                       help="Detener en primer fallo")
    parser.add_argument("--showlocals", "-l", action="store_true", 
                       help="Mostrar variables locales en traceback")
    parser.add_argument("--output", "-o", type=str, 
                       help="Ruta del archivo de salida")
    
    args = parser.parse_args()
    
    # Construir comando pytest
    pytest_args = []
    
    # Verbosidad
    pytest_args.append("-" + "v" * min(args.verbose, 3))
    
    # Seleccionar tests a ejecutar
    if args.performance:
        test_file = PRUEBAS_DIR / TEST_FILES["performance"][0]
        pytest_args.append(str(test_file))  
    elif args.fase:
        for test_file in TEST_FILES[args.fase]:
            pytest_args.append(str(PRUEBAS_DIR / test_file))
    elif args.unit:
        pytest_args.append(str(PRUEBAS_DIR))
        pytest_args.extend(["-m", "not integration"])
    elif args.integration:
        pytest_args.append(str(PRUEBAS_DIR))
        pytest_args.extend(["-m", "integration"])
    elif args.quick:
        pytest_args.append(str(PRUEBAS_DIR))
        pytest_args.extend(["-m", "not slow"])
    elif args.markers:
        pytest_args.append(str(PRUEBAS_DIR))
        pytest_args.extend(["-m", args.markers])
    else:
        # Default: ejecutar todos
        pytest_args.append(str(PRUEBAS_DIR))
    
    # Opciones adicionales
    if args.failfast:
        pytest_args.append("-x")
    
    if args.showlocals:
        pytest_args.append("-l")
    
    if args.coverage:
        pytest_args.extend(["--cov=Aplicacion", "--cov-report=term-missing"])
    
    # Generar reportes
    if args.report == "html":
        output_file = args.output or "test_report.html"
        pytest_args.extend(["--html", output_file, "--self-contained-html"])
        print(f"\nReporte HTML será guardado en: {output_file}")
    elif args.report == "junit":
        output_file = args.output or "test-results.xml"
        pytest_args.extend(["--junit-xml", output_file])
        print(f"\nReporte JUnit será guardado en: {output_file}")
    
    # Agregar configuración por defecto
    pytest_args.append("--tb=short")
    
    # Ejecutar
    returncode = run_pytest(pytest_args)
    
    # Resumen
    print(f"\n{'='*70}")
    if returncode == 0:
        print("TODOS LOS TESTS PASARON")
    else:
        print(f"ALGUNOS TESTS FALLARON (exit code: {returncode})")
    print(f"{'='*70}\n")
    
    return returncode


if __name__ == "__main__":
    sys.exit(main())
