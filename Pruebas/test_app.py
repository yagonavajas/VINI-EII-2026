import pytest
import subprocess
import time
import sys
import os
from pathlib import Path
import urllib.request
import urllib.parse
from SPARQLWrapper import SPARQLWrapper, JSON

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
from Escritorio.queries import SPARQL_QUERIES

BASE_DIR = Path(__file__).resolve().parents[2]
FUSEKI_DIR = os.path.join(root_dir, "Aplicacion", "Apache Jena Fuseki", "apache-jena-fuseki-6.0.0")
FUSEKI_BAT = os.path.join(root_dir, "Aplicacion", "Apache Jena Fuseki", "apache-jena-fuseki-6.0.0", "fuseki-server.bat")
CARGA_SCRIPT = os.path.join(root_dir, "Grafo", "cargaGrafos.py")


FUSEKI_PORT = 3030
ENDPOINT = f"http://localhost:{FUSEKI_PORT}/vini/sparql"
DATASET_NAME = "vini"


# Variables globales para el proceso de Fuseki
_fuseki_process = None

def setup_module():
    """Se ejecuta automáticamente antes de cualquier prueba del módulo"""
    global _fuseki_process


    # 2. Lanzar Fuseki en segundo plano
    _fuseki_process = subprocess.Popen(
        [str(FUSEKI_BAT)],
        cwd=str(FUSEKI_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Esperar a que esté listo
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://localhost:{FUSEKI_PORT}/$/ping", timeout=2):
                break
        except:
            time.sleep(1)
    else:
        _fuseki_process.kill()
        pytest.fail("Fuseki no arrancó a tiempo")

    # 3. Crear dataset (si existe, lo borramos primero)
    _delete_dataset(DATASET_NAME)
    _create_dataset(DATASET_NAME)

    # 4. Ejecutar carga de grafos
    result = subprocess.run(
        [sys.executable, str(CARGA_SCRIPT)],
        cwd=str(CARGA_SCRIPT.parent),
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        _fuseki_process.kill()
        pytest.fail(f"cargaGrafos.py falló:\n{result.stderr}")

def teardown_module():
    """Se ejecuta automáticamente después de todas las pruebas del módulo"""
    global _fuseki_process
    _delete_dataset(DATASET_NAME)
    if _fuseki_process:
        _fuseki_process.terminate()
        try:
            _fuseki_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _fuseki_process.kill()

def _delete_dataset(name):
    url = f"http://localhost:{FUSEKI_PORT}/$/datasets/{name}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

def _create_dataset(name):
    url = f"http://localhost:{FUSEKI_PORT}/$/datasets"
    data = urllib.parse.urlencode({"dbName": name, "dbType": "mem"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"No se pudo crear dataset {name}")

# ------------------------------------------------------------
# Pruebas (sin parámetros)
# ------------------------------------------------------------
def test_dataset_exists():
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setQuery("ASK WHERE { ?s ?p ?o }")
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    assert res["boolean"] is True

def test_graph_loaded():
    sparql = SPARQLWrapper(ENDPOINT)
    query = """
    PREFIX vini: <http://vini-eii.org/>
    ASK { ?teamSeason vini:name ?name }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    assert res["boolean"] is True

def test_champions_query():
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setQuery(SPARQL_QUERIES["champions"])
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    bindings = res["results"]["bindings"]
    assert len(bindings) > 0, "No se obtuvieron ganadores de Champions"
    expected_vars = ["year", "teamName", "overall", "formation"]
    for b in bindings:
        for var in expected_vars:
            assert var in b, f"Falta la variable {var} en {b}"